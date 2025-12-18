from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class SignUpForm(UserCreationForm):
    USER_TYPES = [
        ('farmer', 'Farmer'),
        ('doctor', 'Doctor/Veterinarian'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))

    class Meta(UserCreationForm.Meta):  # type: ignore[attr-defined]
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)  # type: ignore[attr-defined]

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data.get('user_type')
        if user_type == 'farmer':
            user.is_farmer = True
        elif user_type == 'doctor':
            user.is_doctor = True
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    # Standard Django login form
    pass

# --- Append this to core/forms.py ---
from .models import Cattle, FinancialRecord, InventoryItem # Make sure to import these!


CATTLE_BREED_CHOICES = [
    ('Gir', 'Gir'),
    ('Sahiwal', 'Sahiwal'),
    ('Red Sindhi', 'Red Sindhi'),
    ('Kankrej', 'Kankrej'),
    ('Tharparkar', 'Tharparkar'),
    ('Rathi', 'Rathi'),
    ('Holstein Friesian', 'Holstein Friesian'),
    ('Jersey', 'Jersey'),
    ('Murrah', 'Murrah (Buffalo)'),
    ('Mehsana', 'Mehsana (Buffalo)'),
    ('Other', 'Other / Not Listed'),
]

class CattleForm(forms.ModelForm):
    breed = forms.ChoiceField(
        choices=[('', 'Select breed…')] + CATTLE_BREED_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Cattle
        fields = ['tag_number', 'name', 'breed', 'age_years', 'daily_milk_yield', 'last_vaccination_date']
        widgets = {
            'tag_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tag or ear number'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Animal name'}),
            'age_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Age in years'}),
            'daily_milk_yield': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.1, 'placeholder': 'Milk per day'}),
            'last_vaccination_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class FinancialForm(forms.ModelForm):
    class Meta:
        model = FinancialRecord
        fields = ['type', 'amount', 'description']

# core/forms.py
from .models import InventoryItem, InventoryHistory

# Form for Creating a New Item (Initial Setup)
class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'quantity', 'reorder_level', 'daily_usage_rate']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'daily_usage_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5 kg/day'}),
        }

# Form for Adding/Consuming Stock (Transaction)
class StockUpdateForm(forms.Form):
    ACTION_CHOICES = [('ADD', 'Add Stock'), ('CONSUME', 'Record Consumption')]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
    quantity = forms.FloatField(min_value=0.1, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}))
    notes = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional notes (e.g. Morning feed)'}))
    
# --- Append to core/forms.py ---
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body', 'image']
        widgets = {
            'body': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Type your message...',
                'autocomplete': 'off'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }