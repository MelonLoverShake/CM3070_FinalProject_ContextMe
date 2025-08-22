# views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import json
from datetime import datetime
import uuid

def get_authenticated_user(request):
    """Extract and authenticate user from session"""
    supabase_user_raw = request.session.get('supabase_user')
    
    if not supabase_user_raw:
        print("No supabase_user found in session")
        return None
    
    # Parse JSON string to dictionary if it's a string
    if isinstance(supabase_user_raw, str):
        try:
            supabase_user_data = json.loads(supabase_user_raw)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from session: {e}")
            return None
    elif isinstance(supabase_user_raw, dict):
        supabase_user_data = supabase_user_raw
    else:
        print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
        return None
    
    # Extract email and user ID
    email = supabase_user_data.get('email')
    supabase_user_id = supabase_user_data.get('id')
    
    if not email:
        print("No email found in session data")
        return None
    
    # Find the user
    user = None
    try:
        from login.models import User
        user = User.objects.get(email=email)
        print(f"Found user in login.models.User: {user}")
    except Exception as e:
        print(f"Error with login.models.User: {e}")
        try:
            from django.contrib.auth.models import User as DjangoUser
            user = DjangoUser.objects.get(email=email)
            print(f"Found user in Django User: {user}")
        except Exception as e2:
            print(f"Error with Django User: {e2}")
            return None
    
    # Return user object with additional supabase data
    user.supabase_user_id = supabase_user_id
    return user

def consent_view(request):
    """Render the consent page with user data if available."""
    user_data = get_authenticated_user(request)
    
    context = {}
    
    if user_data:
        context.update({
            'username': user_data.username,
            'user_id': user_data.id,
            'supabase_auth_id': getattr(user_data, 'supabase_user_id', None),
        })
    
    return render(request, 'consent.html', context)

@require_http_methods(["POST"])
def record_consent(request):
    """Record user consent in Supabase database"""
    try:
        # Get user data
        user_data = get_authenticated_user(request)
        
        if not user_data:
            return JsonResponse({
                'success': False, 
                'error': 'User not authenticated'
            }, status=401)
        
        # Parse request data
        data = json.loads(request.body)
        consent_type = data.get('consent_type', 'privacy_policy')
        version = data.get('version', '1.0')
        
        # Get the correct user ID from your login_user table
        # The foreign key constraint requires this to be a UUID that exists in login_user table
        login_user_id = None
        
        # If your User model has a UUID field, use that
        if hasattr(user_data, 'id') and isinstance(user_data.id, uuid.UUID):
            login_user_id = str(user_data.id)
        elif hasattr(user_data, 'uuid'):  # Some models use 'uuid' field
            login_user_id = str(user_data.uuid)
        else:
            # If it's an integer ID, we need to find the UUID from login_user table
            try:
                from login.models import User
                login_user = User.objects.get(id=user_data.id)
                # Assuming your User model has a UUID field - adjust field name as needed
                login_user_id = str(login_user.id) if hasattr(login_user, 'id') else str(login_user.uuid)
            except Exception as e:
                print(f"Error finding user UUID: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not find user UUID for foreign key'
                }, status=400)
        
        if not login_user_id:
            return JsonResponse({
                'success': False,
                'error': 'Could not determine user UUID for database insertion'
            }, status=400)
        
        # Prepare consent record to match your exact table structure
        consent_record = {
            # Don't include row_id if it's auto-generated
            'user_id': login_user_id,  # Use the UUID from login_user table
            'consent_type': consent_type,
            'consent_given': True,
            'consent_version': version,
            'consented_at': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4())  # If this is a separate field from row_id
        }
        
        # Insert into Supabase
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Replace 'consent_consent' with your actual table name
        response = requests.post(
            f'{supabase_url}/rest/v1/consent_consent',
            json=consent_record,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print(f"Consent recorded successfully for user {user_data.username}")
            return JsonResponse({
                'success': True,
                'message': 'Consent recorded successfully'
            })
        else:
            print(f"Error recording consent: {response.status_code} - {response.text}")
            return JsonResponse({
                'success': False,
                'error': f'Database error: {response.status_code} - {response.text}'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error in record_consent: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }, status=500)