from rest_framework import generics, permissions
from .models import persona
from .serializers import PersonaSerializer
from django.contrib.auth.models import User
import requests
from django.shortcuts import render
from django.core.exceptions import PermissionDenied



class UserPersonasList(generics.ListAPIView):
    serializer_class = PersonaSerializer

    def get_queryset(self):
  
        user_id = str(self.kwargs.get('user_id'))

        # Grab Supabase user from session
        supabase_user = self.request.session.get('supabase_user')

        supabase_user_id = str(supabase_user.get('id'))

        return persona.objects.filter(user__id=user_id)

class UserPersonaDetail(generics.RetrieveAPIView):
    serializer_class = PersonaSerializer
    lookup_field = 'id'
    queryset = persona.objects.all()



