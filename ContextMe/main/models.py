import uuid
from django.db import models
from login.models import * 

class persona(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personas')

    # Core persona identity
    persona_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    pronouns = models.CharField(max_length=50, blank=True, null=True)
    context = models.CharField(max_length=100, blank=True)

    # Optional profile details
    bio = models.TextField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Privacy & control
    visibility = models.CharField(max_length=50, default='private')
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.persona_name} ({self.context})"