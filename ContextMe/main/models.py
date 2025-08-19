import uuid
from django.db import models
from login.models import * 
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

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

    def create_share_link(self, created_by, expires_in_hours=24, max_views=None, description=""):
        """
        Create a new share link for this persona
        
        Args:
            created_by: User who is creating the share link
            expires_in_hours: How many hours until the link expires (default 24)
            max_views: Optional maximum number of views before link becomes invalid
            description: Optional description for the share link
        
        Returns:
            PersonaShareLink instance
        """
        expires_at = timezone.now() + timedelta(hours=expires_in_hours)
        
        return PersonaShareLink.objects.create(
            persona=self,
            created_by=created_by,
            expires_at=expires_at,
            max_views=max_views,
            description=description
        )

    def get_active_share_links(self):
        """Get all active, non-expired share links for this persona"""
        return self.share_links.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        )

class PersonaShareLink(models.Model):
    """Model to handle secure, expiring persona share links"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona = models.ForeignKey('persona', on_delete=models.CASCADE, related_name='share_links')
    
    # Secure sharing token
    share_token = models.CharField(max_length=64, unique=True, editable=False)
    
    # Link configuration
    expires_at = models.DateTimeField()
    max_views = models.IntegerField(default=None, null=True, blank=True)  # Optional view limit
    current_views = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Optional description for the creator to remember why they shared it
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'persona_share_links'
        indexes = [
            models.Index(fields=['share_token']),
            models.Index(fields=['expires_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if the link has expired"""
        return timezone.now() > self.expires_at

    def is_view_limit_reached(self):
        """Check if view limit has been reached"""
        if self.max_views is None:
            return False
        return self.current_views >= self.max_views

    def is_valid(self):
        """Check if link is valid (not expired, not over view limit, and active)"""
        return (
            self.is_active and 
            not self.is_expired() and 
            not self.is_view_limit_reached()
        )

    def increment_views(self):
        """Increment view count"""
        self.current_views += 1
        self.save(update_fields=['current_views'])

    def get_share_url(self, request=None):
        """Generate the full share URL"""
        if request:
            base_url = request.build_absolute_uri('/')
        else:
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000/')
        
        return f"{base_url.rstrip('/')}/main/persona/shared/{self.share_token}/"

    def __str__(self):
        return f"Share link for {self.persona.persona_name} - expires {self.expires_at}"
