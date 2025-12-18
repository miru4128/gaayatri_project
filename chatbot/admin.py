import json

from django.contrib import admin
from django.utils.html import format_html

from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
	model = ChatMessage
	extra = 0
	readonly_fields = ('role', 'text', 'location', 'feedback', 'created_at')
	fields = ('role', 'text', 'location', 'feedback', 'created_at')
	can_delete = False
	show_change_link = True


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'created_at', 'context_summary', 'message_count')
	list_filter = ('created_at',)
	search_fields = ('user__username', 'user__first_name', 'user__last_name')
	readonly_fields = ('user', 'created_at', 'context_display')
	inlines = [ChatMessageInline]

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.prefetch_related('messages', 'user')

	def message_count(self, obj):
		return obj.messages.count()

	message_count.short_description = 'Messages'

	def context_summary(self, obj):
		context = obj.context or {}
		pieces = []
		for key in ('name', 'tag_number', 'breed', 'issue'):
			value = context.get(key)
			if value:
				pieces.append(f"{key.replace('_', ' ').title()}: {value}")
		return ', '.join(pieces) if pieces else '—'

	context_summary.short_description = 'Context'

	def context_display(self, obj):
		if not obj.context:
			return 'No context recorded'
		data = json.dumps(obj.context, indent=2, ensure_ascii=False)
		return format_html('<pre style="white-space: pre-wrap;">{}</pre>', data)

	context_display.short_description = 'Context JSON'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'session', 'role', 'short_text', 'created_at')
	list_filter = ('role', 'created_at')
	search_fields = ('text', 'session__user__username')
	readonly_fields = ('session', 'role', 'text', 'location', 'feedback', 'created_at')

	def short_text(self, obj):
		return (obj.text[:60] + '…') if len(obj.text) > 60 else obj.text

	short_text.short_description = 'Text'
from django.contrib import admin

# Register your models here.
