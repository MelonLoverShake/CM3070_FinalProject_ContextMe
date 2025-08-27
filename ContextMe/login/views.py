# Standard Library Imports
import uuid
import hashlib
import requests

# Django Core Imports
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

# Django Views & Auth
from django.views import View
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.hashers import check_password

# Third-Party Libraries
from supabase import create_client, Client

# Local App Imports
from .forms import *
from .models import User
from main.models import persona
from .utils import get_client_ip, get_user_agent_info
from .permission import BlocklistPermission
from .services.supabase_auth import SupabaseAuth
from .supabase_cilent import supabase

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
from django.http import HttpResponse
from django.db import transaction

@ratelimit(key="ip", rate='10/m',block=True)
def login_view(request):
    permission_classes = [BlocklistPermission]
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Your existing Supabase password check logic here
            try:
                response = supabase.table('login_user').select('*').eq('email', email).execute()
                if not response.data:
                    messages.error(request, 'Invalid email or password.')
                    return render(request, 'login.html', {'form': form})

                user_data = response.data[0]
                stored_password = user_data.get('password')

                from django.contrib.auth.hashers import check_password

                if stored_password:
                    password_match = check_password(password, stored_password)
                    if not password_match:
                        if password != stored_password:
                            messages.error(request, 'Invalid email or password.')
                            return render(request, 'login.html', {'form': form})
                else:
                    messages.error(request, 'Invalid email or password.')
                    return render(request, 'login.html', {'form': form})

            except Exception as e:
                messages.error(request, 'Login failed. Please try again.')
                return render(request, 'login.html', {'form': form})

            # If password valid, send OTP
            supabase_auth = SupabaseAuth()
            result = supabase_auth.send_otp(email)

            if result['success']:
                request.session['otp_email'] = email
                messages.success(request, 'Password verified! Check your email for the login code.')
                return redirect('verify_otp')
            else:
                messages.error(request, f"Error sending OTP: {result['error']}")
                return render(request, 'login.html', {'form': form})

        else:
            # This triggers if captcha fails or form invalid
            messages.error(request, 'Please complete the captcha correctly.')
            return render(request, 'login.html', {'form': form})

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

@ratelimit(key="ip", rate='10/m',block=True)
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
                        'last_login_time': now
                    }).eq('email', email).execute()

                    print("[DEBUG] Supabase update response:", update_response)
                except Exception as e:
                    print("[ERROR] Failed to update Supabase:", e)

                # ✅ LOG SUCCESSFUL LOGIN ACTIVITY
                try:
                    from log.models import ActivityLog
                    django_user = None
                    try:
                        # If you have a Django User model that corresponds to Supabase users
                        django_user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        pass

                    with transaction.atomic():
                        activity_log = ActivityLog.objects.create(
                            user=django_user,  # Will be None if no Django user found
                            persona=None,  # No specific persona for login
                            action_type='LOGIN',
                            description=f"User '{email}' successfully logged in via OTP verification",
                            ip_address=ip,
                            # You might want to add additional fields like user_agent if your model supports it
                        )
                    
                    print(f"✅ Login activity logged successfully: User {email}, Log ID: {activity_log.id}")
                    
                except Exception as log_error:
                    print(f"❌ Failed to log login activity for {email}: {log_error}")
                    import traceback
                    traceback.print_exc()

                del request.session['otp_email']
                messages.success(request, 'Welcome back!')
                return redirect('dashboard')
            else:
                # ✅ LOG FAILED LOGIN ATTEMPT
                try:
                    # Try to get Django User object for failed login logging
                    django_user = None
                    try:
                        django_user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        pass

                    with transaction.atomic():
                        activity_log = ActivityLog.objects.create(
                            user=django_user,  
                            persona=None,
                            action_type='LOGIN_FAILED',
                            description=f"Failed OTP verification for '{email}': {result['error']}",
                            ip_address=get_client_ip(request),
                        )
                    
                    print(f"⚠️ Failed login attempt logged: User {email}, Log ID: {activity_log.id}")
                    
                except Exception as log_error:
                    print(f"❌ Failed to log failed login attempt for {email}: {log_error}")
                    import traceback
                    traceback.print_exc()

                messages.error(request, f"Invalid code: {result['error']}")
    else:
        form = OTPForm()

    return render(request, 'verify_otp.html', {'form': form, 'email': email})

@ratelimit(key="ip", rate='10/m',block=True)
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


@ratelimit(key="ip", rate='10/m', block=True)
def dashboard_view(request):
    supabase_user = request.session.get('supabase_user')
    supabase_token = request.session.get('supabase_token')

    if not supabase_token or not supabase_user:
        messages.error(request, 'You must be logged in.')
        return redirect('login')

    user_email = supabase_user.get('email')
    supabase_auth_id = supabase_user.get('id')

    # Fetch user data from Supabase
    url = f"{settings.SUPABASE_URL}/rest/v1/login_user?email=eq.{user_email}"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {supabase_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers)

    username = None
    user_id = None
    personas = []
    
    if response.status_code == 200:
        data = response.json()
        if data:
            username = data[0].get('username')
            user_id = data[0].get('id')

    # Fetch personas for this user
    try:
        # Get the session data for personas (similar to PersonaList logic)
        supabase_user_raw = request.session.get('supabase_user')
        
        if supabase_user_raw:
            # Parse JSON string to dictionary if it's a string
            if isinstance(supabase_user_raw, str):
                try:
                    supabase_user_data = json.loads(supabase_user_raw)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from session: {e}")
                    supabase_user_data = supabase_user_raw
            elif isinstance(supabase_user_raw, dict):
                supabase_user_data = supabase_user_raw
            else:
                supabase_user_data = supabase_user_raw

            # Extract email for persona lookup
            email = supabase_user_data.get('email') if isinstance(supabase_user_data, dict) else user_email
            
            if email:
                # Find the user for personas
                user = None
                try:
                    # Try your custom User model first
                    from login.models import User
                    user = get_object_or_404(User, email=email)
                    print(f"Found user in login.models.User: {user}")
                except Exception as e:
                    print(f"Error with login.models.User: {e}")
                    try:
                        # Fallback to Django's built-in User model
                        from django.contrib.auth.models import User as DjangoUser
                        user = get_object_or_404(DjangoUser, email=email)
                        print(f"Found user in Django User: {user}")
                    except Exception as e2:
                        print(f"Error with Django User: {e2}")
                        user = None

                # Fetch personas if user found
                if user:
                    try:
                        # Filter for active personas only
                        personas = persona.objects.filter(user=user, is_active=True).order_by('-created_at')
                        print(f"Found {personas.count()} active personas for user {user}")
                    except Exception as e:
                        print(f"Error fetching personas: {e}")
                        personas = []
                        
    except Exception as e:
        print(f"Error fetching personas in dashboard: {e}")
        personas = []

    return render(request, 'dashboard.html', {
        'username': username or user_email,
        'user_id': user_id,
        'supabase_auth_id': supabase_auth_id,
        'personas': personas,
        'personas_count': len(personas) if personas else 0,
    })
    
@ratelimit(key="ip", rate='10/m',block=True)
def logout_view(request):
    user = None
    # Try to get the user before clearing the session 
    try:
        supabase_user_raw = request.session.get('supabase_user')
        
        if supabase_user_raw:
            # Parse JSON string to dictionary if it's a string
            if isinstance(supabase_user_raw, str):
                try:
                    supabase_user_data = json.loads(supabase_user_raw)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from session: {e}")
                    supabase_user_data = None
            elif isinstance(supabase_user_raw, dict):
                supabase_user_data = supabase_user_raw
            else:
                print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
                supabase_user_data = None
            
            # Extract email and find user
            if supabase_user_data:
                email = supabase_user_data.get('email')
                
                if email:
                    try:
                        from login.models import User
                        user = User.objects.filter(email=email).first()
                        if not user:
                            from django.contrib.auth.models import User as DjangoUser
                            user = DjangoUser.objects.filter(email=email).first()
                    except Exception as e:
                        print(f"Error finding user for logout logging: {e}")
                        user = None
    
    except Exception as e:
        print(f"Error extracting user data for logout logging: {e}")
    
    # Log the logout activity before clearing the session
    if user:
        try:
            from log.models import ActivityLog
            from django.db import transaction
            
            # Get client IP address
            def get_client_ip(request):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                return ip
            
            with transaction.atomic():
                activity_log = ActivityLog.objects.create(
                    user=user,
                    persona=None,  # No specific persona for logout
                    action_type='LOGOUT',
                    description=f"User '{user.email if hasattr(user, 'email') else user.username}' logged out",
                    ip_address=get_client_ip(request)
                )
            
            print(f"✅ Activity logged successfully: User logout, Log ID: {activity_log.id}")
            
        except Exception as log_error:
            print(f"❌ Failed to log logout activity: {log_error}")
            import traceback
            traceback.print_exc()
    
    # Clear the session
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@ratelimit(key="ip", rate='10/m',block=True)
def user_profile_view(request):
    # ---------- Existing user retrieval logic ----------
    user_email = None
    supabase_user = request.session.get('supabase_user')
    if supabase_user:
        if isinstance(supabase_user, dict):
            user_email = supabase_user.get('email')
        elif isinstance(supabase_user, str):
            import json
            try:
                user_data = json.loads(supabase_user)
                user_email = user_data.get('email')
            except json.JSONDecodeError:
                pass
    if not user_email:
        user_email = request.session.get('user_email') or request.session.get('email')
    
    if user_email:
        try:
            user_profile = get_object_or_404(LoginUser, email=user_email)
        except:
            user_profile = get_object_or_404(User, email=user_email)
    else:
        if request.user.is_authenticated:
            user_profile = request.user
        else:
            from django.shortcuts import redirect
            return redirect('login')

    user_has_consent = check_user_consent(user_profile) if user_profile else False

    # ---------- NEW: handle image upload ----------
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['image']

            # Upload directly to Cloudinary
            response = cloudinary.uploader.upload(file)
            direct_link = response['secure_url']

            # Save link in Supabase (example table: 'user_images')
            supabase.table("user_images").insert({
                "user_email": user_email,
                "image_url": direct_link
            }).execute()
            
            return redirect('user_profile')  # refresh to show new image
    else:
        form = ImageUploadForm()
        
    images = supabase.table("user_images").select("*").eq("user_email", user_email).execute().data

    return render(request, 'profile.html', {
        'user': user_profile,
        'user_has_consent': user_has_consent,
        'form': form,
        'images': images
    })

def check_user_consent(user_profile):
    """
    Check if user has given consent by querying Supabase consent_consent table
    """
    try:
        # Get the user ID that should be in the consent table
        # This should match what you used in the consent recording
        if hasattr(user_profile, 'id'):
            if isinstance(user_profile.id, uuid.UUID):
                user_id = str(user_profile.id)
            else:
                # Try to get UUID from login_user table
                try:
                    from login.models import User as LoginUser
                    login_user = LoginUser.objects.get(id=user_profile.id)
                    user_id = str(login_user.id)
                except Exception as e:
                    print(f"Error finding user UUID for consent check: {e}")
                    user_id = str(user_profile.id)
        else:
            return False
        
        # Query Supabase consent_consent table
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Query for consent records for this user
        params = {
            'user_id': f'eq.{user_id}',
            'consent_given': 'eq.true',
            'consent_type': 'eq.privacy_policy'
        }
        
        response = requests.get(
            f'{supabase_url}/rest/v1/consent_consent',
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            consent_records = response.json()
            return len(consent_records) > 0
        else:
            print(f"Error checking consent: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error in check_user_consent: {str(e)}")
        return False

def change_password_view(request):
    # ✅ Ensure user is logged in via Supabase session
    if 'supabase_user' not in request.session:
        messages.error(request, 'Please log in to change your password.')
        return redirect('login')

    # ✅ Get email from Supabase session
    user_data = request.session['supabase_user']
    email = user_data.get('email')

    if not email:
        messages.error(request, 'Missing session email. Please log in again.')
        return redirect('login')

    # ✅ Find user in Django by email (since UUID might not match Supabase's user.id)
    user = get_object_or_404(User, email=email)

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # ✅ Validate current password
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'change_password.html', {'user': user})

        # ✅ Validate new password requirements
        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return render(request, 'change_password.html', {'user': user})

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'change_password.html', {'user': user})

        if user.check_password(new_password):
            messages.error(request, 'New password must be different from current password.')
            return render(request, 'change_password.html', {'user': user})

        # ✅ Set and save new password with timestamp
        user.set_password(new_password)
        user.last_password_change = timezone.now()
        user.save()
        print(new_password)

        messages.success(request, 'Password changed successfully!')
        return redirect('dashboard')

    return render(request, 'change_password.html', {'user': user})

def user_download_view(request):
     # ✅ Get email from Supabase session
    user_data = request.session['supabase_user']
    email = user_data.get('email')

    user = get_object_or_404(User, email=email)

    return render(request, 'download.html', {'user': user})

@ratelimit(key="ip", rate='10/m',block=True)
def download_user_data_txt(request):
    """
    Download user data as a text file
    """
    user_data = request.session['supabase_user']

    email = user_data.get('email')

    user = get_object_or_404(User, email=email)
    
    # Format the user data
    content = f"""USER DATA EXPORT
Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}
PERSONAL INFORMATION
{'='*50}

Username: {user.username}
Email: {user.email}
First Name: {user.first_name or 'Not provided'}
Last Name: {user.last_name or 'Not provided'}
Pronouns: {user.pronouns or 'Not provided'}
Gender Identity: {user.gender_identity or 'Not provided'}

{'='*50}
ACCOUNT INFORMATION
{'='*50}

Account ID: {user.id}
Account Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'Not available'}
Last Updated: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'Not available'}
Last Login Browser: {user.last_login_browser or 'Not available'}
Last Password Change: {user.last_password_change.strftime('%Y-%m-%d %H:%M:%S') if user.last_password_change else 'Not available'}

{'='*50}
END OF EXPORT
{'='*50}

This file contains your personal data as stored in our system.
For questions about your data, please contact support.
"""

    # Create response
    response = HttpResponse(content, content_type='text/plain')
    filename = f'user_data_{user.username}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@ratelimit(key="ip", rate='10/m',block=True)
def download_user_data_pdf(request):
    """
    Download user data as a PDF file
    """
    user_data = request.session['supabase_user']

    email = user_data.get('email')

    user = get_object_or_404(User, email=email)
    
    # Create a BytesIO buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor='#2c3e50'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor='#34495e'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        leftIndent=20
    )
    
    # Add content
    elements.append(Paragraph("USER DATA EXPORT", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Personal Information Section
    elements.append(Paragraph("PERSONAL INFORMATION", heading_style))
    elements.append(Paragraph(f"<b>Username:</b> {user.username}", normal_style))
    elements.append(Paragraph(f"<b>Email:</b> {user.email}", normal_style))
    elements.append(Paragraph(f"<b>First Name:</b> {user.first_name or 'Not provided'}", normal_style))
    elements.append(Paragraph(f"<b>Last Name:</b> {user.last_name or 'Not provided'}", normal_style))
    elements.append(Paragraph(f"<b>Pronouns:</b> {user.pronouns or 'Not provided'}", normal_style))
    elements.append(Paragraph(f"<b>Gender Identity:</b> {user.gender_identity or 'Not provided'}", normal_style))
    
    # Account Information Section
    elements.append(Paragraph("ACCOUNT INFORMATION", heading_style))
    elements.append(Paragraph(f"<b>Account ID:</b> {user.id}", normal_style))
    elements.append(Paragraph(f"<b>Account Created:</b> {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'Not available'}", normal_style))
    elements.append(Paragraph(f"<b>Last Updated:</b> {user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'Not available'}", normal_style))
    elements.append(Paragraph(f"<b>Last Login Browser:</b> {user.last_login_browser or 'Not available'}", normal_style))
    elements.append(Paragraph(f"<b>Last Password Change:</b> {user.last_password_change.strftime('%Y-%m-%d %H:%M:%S') if user.last_password_change else 'Not available'}", normal_style))
    
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("This file contains your personal data as stored in our system.", normal_style))
    elements.append(Paragraph("For questions about your data, please contact support.", normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'user_data_{user.username}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def settings_account_view(request):
    return render(request, 'settings.html')

def delete_account_form_view(request):
    """Handle account deletion via form submission"""
    try:
        # Use your exact pattern
        user_data = request.session['supabase_user']
        email = user_data.get('email')
        user = get_object_or_404(User, email=email)
        
        # Get Supabase user ID for auth deletion
        user_id = user_data.get('id')

        try:
            result = supabase.table('login_user').delete().eq('email', email).execute()
            print(f"Successfully deleted user data from users table: {email}")
            
        except Exception as table_error:
            print(f"Error deleting from users table for {email}: {type(table_error).__name__}: {str(table_error)}")
            messages.error(request, f'Error deleting user data: {str(table_error)}')
            return redirect('settings_account')
        
        # Delete Django user
        try:
            user.delete()
            print(f"Successfully deleted Django user: {email}")
        except Exception as django_error:
            print(f"Error deleting Django user {email}: {type(django_error).__name__}: {str(django_error)}")
            messages.error(request, f'Error deleting Django user: {str(django_error)}')
            return redirect('settings_account')
        
        # Clear session
        try:
            request.session.flush()
            print(f"Successfully cleared session for user: {email}")
        except Exception as session_error:
            print(f"Error clearing session: {type(session_error).__name__}: {str(session_error)}")
            
        messages.success(request, 'Your account has been successfully deleted.')
        print(f"Account deletion completed successfully for user: {email}")
        return redirect('/')
            
    except KeyError as key_error:
        print(f"KeyError - User session not found: {str(key_error)}")
        messages.error(request, 'User session not found')
        return redirect('settings_account')
    except Exception as unexpected_error:
        print(f"Unexpected error during account deletion: {type(unexpected_error).__name__}: {str(unexpected_error)}")
        messages.error(request, f'An unexpected error occurred: {str(unexpected_error)}')
        return redirect('settings_account')