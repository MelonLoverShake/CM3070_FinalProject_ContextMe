from django.shortcuts import render
from django.conf import settings
import requests


def get_user_data_from_supabase(request):
    """
    Helper function to retrieve user data from Supabase.
    Returns a dictionary with user information or None if not authenticated.
    """
    supabase_user = request.session.get('supabase_user')
    supabase_token = request.session.get('supabase_token')

    if not supabase_token or not supabase_user:
        return None

    user_email = supabase_user.get('email')
    supabase_auth_id = supabase_user.get('id')  

    url = f"{settings.SUPABASE_URL}/rest/v1/login_user?email=eq.{user_email}"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {supabase_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers)

    username = None
    user_id = None  # This will be the actual user ID from your login_user table
    
    if response.status_code == 200:
        data = response.json()
        if data:
            username = data[0].get('username')
            user_id = data[0].get('id')  # Get the actual user ID from login_user table

    return {
        'username': username or user_email,
        'user_id': user_id,
        'supabase_auth_id': supabase_auth_id,
        'user_email': user_email,
        'supabase_token': supabase_token,
    }

def consent_view(request):
    """
    Render the consent page with user data if available.
    """
    user_data = get_user_data_from_supabase(request)
    
    context = {}
    
    if user_data:
        context.update({
            'username': user_data['username'],
            'user_id': user_data['user_id'],
            'supabase_auth_id': user_data['supabase_auth_id'],
        })
    
    return render(request, 'consent.html', context)