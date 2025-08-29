import uuid
from django.db import models
from django.contrib.auth.hashers import check_password

class Admin_users(models.Model):
    admin_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_level = models.IntegerField(default=1)
    security_QAns = models.TextField(editable=True)

    def check_password(self, raw_password):
        """Check if the provided password is correct"""
        return check_password(raw_password, self.password)

    def check_SecurityQ(self, raw_SecurityQ):
        return(raw_SecurityQ, self.security_QAns)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'admin_users'