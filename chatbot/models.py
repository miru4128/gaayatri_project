from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    context = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"ChatSession:{self.user.id}:{self.created_at.isoformat()}"


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=(('user', 'user'), ('bot', 'bot')))
    text = models.TextField()
    # optional location info (JSON string or short text)
    location = models.CharField(max_length=250, blank=True, null=True)
    # user feedback: -1 (bad), 0 (none), 1 (good)
    feedback = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.text[:40]}"

