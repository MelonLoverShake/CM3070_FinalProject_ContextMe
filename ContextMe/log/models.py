import uuid
from django.db import models
from login.models import User
from main.models import persona

class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    persona = models.ForeignKey(persona, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')

    # Action details
    action_type = models.CharField(max_length=100)  # e.g. "LOGIN", "CREATE_PERSONA", "DELETE_ACCOUNT"
    description = models.TextField(blank=True, null=True)  # human-readable description of the action

    # Context info
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_log'
        ordering = ['-created_at']

    def __str__(self):
        if self.persona:
            return f"{self.user.username} ({self.persona.persona_name}) - {self.action_type}"
        return f"{self.user.username} - {self.action_type}"
