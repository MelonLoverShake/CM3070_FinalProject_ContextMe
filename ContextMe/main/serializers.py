from rest_framework import serializers
from .models import persona

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = persona
        fields = [
            'id', 'persona_name', 'username', 'pronouns', 'context', 'bio',
            'avatar_url', 'email', 'phone', 'visibility', 'is_active',
            'created_at', 'updated_at'
        ]
