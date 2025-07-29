from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    """
    Full serializer for User model with all fields
    """
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'last_login_browser', 'created_at', 'updated_at', 'pronouns', 'gender_identity', 'last_password_change'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
    
    def create(self, validated_data):
        """
        Create user with hashed password
        """
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update user, hash password if provided
        """
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

