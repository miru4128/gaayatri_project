# core/views.py
from datetime import datetime
from typing import Dict, Tuple

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Sum

from chatbot.models import ChatSession, ChatMessage

from .forms import SignUpForm, LoginForm, CattleForm, FinancialForm
from .forms import InventoryItemForm, StockUpdateForm
from .models import Cattle, FinancialRecord, InventoryItem, InventoryHistory


def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def farmer_dashboard(request):
    return render(request, 'core/farmer_dashboard.html')

@login_required
def doctor_dashboard(request):
    return render(request, 'core/doctor_dashboard.html')


def _summarize_cattle_context(context):
    if not context:
        return "No cattle details recorded"
    parts = []
    name = context.get('name')
    tag = context.get('tag_number')
    if name and tag:
        parts.append(f"{name} (Tag {tag})")
    elif name:
        parts.append(str(name))
    elif tag:
        parts.append(f"Tag {tag}")
    if context.get('breed'):
        parts.append(f"Breed: {context['breed']}")
    if context.get('milk_yield'):
        parts.append(f"Yield: {context['milk_yield']} L/day")
    if context.get('age_years'):
        parts.append(f"Age: {context['age_years']} years")
    if context.get('issue'):
        parts.append(f"Issue: {context['issue']}")
    if not parts:
        return "No cattle details recorded"
    return " | ".join(parts)


def _context_items(context):
    labels = [
        ('Name', 'name'),
        ('Tag #', 'tag_number'),
        ('Breed', 'breed'),
        ('Age (years)', 'age_years'),
        ('Milk yield (L/day)', 'milk_yield'),
        ('Lactation stage', 'lactation_stage'),
        ('Primary issue', 'issue'),
        ('Notes', 'notes'),
        ('Last vaccination', 'last_vaccination_date'),
        ('Under treatment', 'is_sick'),
    ]
    items = []
    for label, key in labels:
        value = context.get(key)
        if value in (None, '', []):
            continue
        display = value
        if key == 'age_years' and isinstance(value, (int, float)):
            display = f"{value} years"
        elif key == 'milk_yield' and isinstance(value, (int, float)):
            display = f"{value} L/day"
        elif key == 'last_vaccination_date':
            try:
                display = datetime.fromisoformat(str(value)).strftime('%b %d, %Y')
            except ValueError:
                display = str(value)
        elif key == 'is_sick':
            display = 'Yes' if bool(value) else 'No'
        items.append((label, display))
    return items


@login_required
def doctor_chat_history(request):
    if not getattr(request.user, 'is_doctor', False):
        return redirect('doctor_dashboard')

    message_prefetch = Prefetch(
        'messages',
        queryset=ChatMessage.objects.order_by('created_at'),
        to_attr='ordered_messages',
    )

    sessions = (
        ChatSession.objects.select_related('user')
        .filter(user__is_farmer=True)
        .prefetch_related(message_prefetch)
        .order_by('-created_at')
    )

    cattle_lookup: Dict[Tuple[int, int], Cattle] = {}
    candidate_pairs = set()
    for session in sessions:
        context = session.context or {}
        animal_id = context.get('animal_id')
        if animal_id in (None, ''):
            continue
        try:
            animal_pk = int(animal_id)
        except (TypeError, ValueError):
            continue
        owner_pk = getattr(session.user, 'pk', None)
        if owner_pk is None:
            continue
        candidate_pairs.add((owner_pk, animal_pk))

    if candidate_pairs:
        owner_ids = {owner_id for owner_id, _ in candidate_pairs}
        cattle_ids = {animal_pk for _, animal_pk in candidate_pairs}
        cattle_queryset = (
            Cattle.objects.filter(owner_id__in=owner_ids, pk__in=cattle_ids)
            .select_related('owner')
        )
        for cattle in cattle_queryset:
            owner_pk = getattr(cattle.owner, 'pk', None)
            if owner_pk is None:
                continue
            cattle_lookup[(owner_pk, cattle.pk)] = cattle

    session_data = []
    for session in sessions:
        context = session.context or {}
        messages = list(getattr(session, 'ordered_messages', []))
        last_message_at = messages[-1].created_at if messages else session.created_at

        cattle_obj = None
        animal_id = context.get('animal_id')
        if animal_id not in (None, ''):
            try:
                animal_pk = int(animal_id)
            except (TypeError, ValueError):
                animal_pk = None
            if animal_pk:
                owner_pk = getattr(session.user, 'pk', None)
                if owner_pk is not None:
                    cattle_obj = cattle_lookup.get((owner_pk, animal_pk))

        session_data.append({
            'session': session,
            'farmer': session.user,
            'context': context,
            'context_summary': _summarize_cattle_context(context),
            'context_items': _context_items(context),
            'cattle': cattle_obj,
            'messages': messages,
            'last_message_at': last_message_at,
            'message_count': len(messages),
            'started_at': session.created_at,
        })

    return render(request, 'core/doctor_chat_history.html', {
        'session_data': session_data,
    })


@login_required
def manage_cattle(request):
    editing_cattle = None

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            cattle = get_object_or_404(Cattle, pk=request.POST.get('delete_id'), owner=request.user)
            cattle.delete()
            return redirect('manage_cattle')

        cattle_id = request.POST.get('cattle_id')
        if cattle_id:
            editing_cattle = get_object_or_404(Cattle, pk=cattle_id, owner=request.user)

        form = CattleForm(request.POST, instance=editing_cattle)
        if form.is_valid():
            cattle = form.save(commit=False)
            cattle.owner = request.user
            cattle.save()
            return redirect('manage_cattle')
    else:
        edit_id = request.GET.get('edit')
        if edit_id:
            editing_cattle = get_object_or_404(Cattle, pk=edit_id, owner=request.user)
            form = CattleForm(instance=editing_cattle)
        else:
            form = CattleForm()

    cattle_list = Cattle.objects.filter(owner=request.user).order_by('name')
    return render(request, 'core/manage_cattle.html', {
        'cattle_list': cattle_list,
        'form': form,
        'editing_cattle': editing_cattle,
    })

@login_required
def performance(request):
    if request.method == 'POST':
        form = FinancialForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            return redirect('performance')
    else:
        form = FinancialForm()
    records = FinancialRecord.objects.filter(user=request.user).order_by('-date')
    total_income = records.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = records.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = total_income - total_expense
    return render(request, 'core/performance.html', {
        'records': records, 'form': form,
        'total_income': total_income, 'total_expense': total_expense, 'net_profit': net_profit
    })


@login_required
def inventory(request):
    """View current stock, days remaining, and add new items"""
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            # Create initial history log
            InventoryHistory.objects.create(
                item=item, action='ADD', quantity_changed=item.quantity, notes="Initial Stock"
            )
            return redirect('inventory')
    else:
        form = InventoryItemForm()
        
    items = InventoryItem.objects.filter(user=request.user)
    return render(request, 'core/inventory.html', {'items': items, 'form': form})

@login_required
def update_inventory(request, pk):
    """Handle Adding or Consuming stock with History"""
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    history = InventoryHistory.objects.filter(item=item).order_by('-date')[:10]

    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            qty = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']

            # Update the main item quantity
            if action == 'ADD':
                item.quantity += qty
            elif action == 'CONSUME':
                if item.quantity >= qty:
                    item.quantity -= qty
                else:
                    form.add_error('quantity', 'Not enough stock to consume this amount!')
                    return render(request, 'core/update_inventory.html', {'form': form, 'item': item, 'history': history})

            item.save()

            # Create History Record
            InventoryHistory.objects.create(
                item=item, action=action, quantity_changed=qty, notes=notes
            )
            return redirect('inventory')
    else:
        form = StockUpdateForm()

    return render(request, 'core/update_inventory.html', {'form': form, 'item': item, 'history': history})

# --- Append to core/views.py ---
from .models import Message, User
from .forms import MessageForm
from django.db.models import Q

@login_required
def doctor_list(request):
    """List all registered doctors for the farmer to contact"""
    doctors = User.objects.filter(is_doctor=True)
    return render(request, 'core/doctor_list.html', {'doctors': doctors})

@login_required
def chat_view(request, user_id):
    """Chat room between current user and another user (user_id)"""
    other_user = get_object_or_404(User, pk=user_id)
    
    # Fetch conversation history
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = other_user
            message.save()
            return redirect('chat_view', user_id=user_id)
    else:
        form = MessageForm()

    return render(request, 'core/chat.html', {
        'other_user': other_user, 
        'messages': messages, 
        'form': form
    })

@login_required
def inbox(request):
    """List of people who have exchanged messages with the current user"""
    # Get all unique users involved in messages with me
    sent_to = Message.objects.filter(sender=request.user).values_list('recipient', flat=True)
    received_from = Message.objects.filter(recipient=request.user).values_list('sender', flat=True)
    
    contact_ids = set(list(sent_to) + list(received_from))
    contacts = User.objects.filter(id__in=contact_ids)
    
    return render(request, 'core/inbox.html', {'contacts': contacts})

