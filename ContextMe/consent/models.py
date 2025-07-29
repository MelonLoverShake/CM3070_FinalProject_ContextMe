# app/models.py
from django.db import models

class Consent(models.Model):
    user_id = models.UUIDField()  
    consent_type = models.CharField(max_length=100) 
    consent_given = models.BooleanField(default=False)
    consent_version = models.CharField(max_length=20, default='v1')
    consented_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'consent_type', 'consent_version')

    def __str__(self):
        return f"{self.user_id} - {self.consent_type} ({self.consent_version})"

