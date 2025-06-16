import uuid
from django.db import models

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID as primary key
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, null=True, blank=True)
    last_login_os = models.CharField(max_length=255, null=True, blank=True)
    last_login_browser = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pronouns = models.CharField(max_length=50, blank=True)
    gender_identity = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.username

class Blocklist(models.Model):
    ip_addr = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Blocked: {self.ip_addr}"

    class Meta:
        verbose_name = "Blocked IP"
        verbose_name_plural = "Blocked IPs"


