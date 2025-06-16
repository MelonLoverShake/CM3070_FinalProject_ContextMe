from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import *
from .models import User
from .utils import get_client_ip, get_user_agent_info
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.hashers import check_password  
import uuid
from django.shortcuts import render, get_object_or_404
from .services.supabase_auth import SupabaseAuth
from django.conf import settings
import requests
from django.utils import timezone
from .permission import BlocklistPermission


def login_view(request):
    permission_classes = [BlocklistPermission]
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Send OTP
            supabase_auth = SupabaseAuth()
            result = supabase_auth.send_otp(email)
            
            if result['success']:
                # Store email in session for verification step
                request.session['otp_email'] = email
                messages.success(request, 'Check your email for the login code!')
                return redirect('verify_otp')
            else:
                messages.error(request, f"Error: {result['error']}")
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def verify_otp_view(request):
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, 'Please enter your email first.')
        return redirect('login')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            supabase_auth = SupabaseAuth()
            result = supabase_auth.verify_otp(email, otp_code)

            if result['success']:
                user_data = result['data'].get('user', {})
                token = result['data'].get('access_token')

                if not token:
                    messages.error(request, "Missing token in response.")
                    return redirect('verify_otp')

                # Save user & token to session
                request.session['supabase_token'] = token
                request.session['supabase_user'] = user_data

                # Gather metadata
                ip = get_client_ip(request)
                ua = get_user_agent_info(request)
                now = timezone.now().isoformat()

                # ✅ UPDATE SUPABASE RECORD
                try:
                    update_response = supabase.table('login_user').update({
                        'last_login_ip': ip,
                        'device': ua['device'],
                        'os': ua['os'],
                        'browser': ua['browser'],
                        'last_login_time': now
                    }).eq('email', email).execute()

                    print("[DEBUG] Supabase update response:", update_response)
                except Exception as e:
                    print("[ERROR] Failed to update Supabase:", e)

                del request.session['otp_email']
                messages.success(request, 'Welcome back!')
                return redirect('dashboard')
            else:
                messages.error(request, f"Invalid code: {result['error']}")
    else:
        form = OTPForm()

    return render(request, 'verify_otp.html', {'form': form, 'email': email})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})



def dashboard_view(request):
    supabase_user = request.session.get('supabase_user')
    supabase_token = request.session.get('supabase_token')

    if not supabase_token or not supabase_user:
        messages.error(request, 'You must be logged in.')
        return redirect('login')

    user_email = supabase_user.get('email')
    supabase_auth_id = supabase_user.get('id')  # This is the auth ID

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

    return render(request, 'dashboard.html', {
        'username': username or user_email,
        'user_id': user_id,  # Use this instead of supabase_user_id
        'supabase_auth_id': supabase_auth_id,  # Keep this if you need the auth ID
    })


def logout_view(request):
    # Clear the session
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

def user_profile_view(request):
    # Try to get email from different possible session keys
    user_email = None
    
    # Check if supabase_user contains email info
    supabase_user = request.session.get('supabase_user')
    if supabase_user:
        # If supabase_user is a dict, get email from it
        if isinstance(supabase_user, dict):
            user_email = supabase_user.get('email')
        # If it's a string (JSON), parse it first
        elif isinstance(supabase_user, str):
            import json
            try:
                user_data = json.loads(supabase_user)
                user_email = user_data.get('email')
            except json.JSONDecodeError:
                pass
    
    # Fallback: check if email is directly stored in session
    if not user_email:
        user_email = request.session.get('user_email') or request.session.get('email')
    
    # If we found an email, look up the user in login_user table
    if user_email:
        try:
            user_profile = get_object_or_404(LoginUser, email=user_email)
        except:
            # Fallback to Django's built-in User model if LoginUser doesn't exist
            user_profile = get_object_or_404(User, email=user_email)
    else:
        # Final fallback to authenticated user
        if request.user.is_authenticated:
            user_profile = request.user
        else:
            # Redirect to login if no user info found
            from django.shortcuts import redirect
            return redirect('login') 
    
    return render(request, 'profile.html', {'user_profile': user_profile})