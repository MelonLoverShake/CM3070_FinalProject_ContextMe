from rest_framework import generics, permissions
from .models import persona, PersonaShareLink
from .serializers import PersonaSerializer
from django.contrib.auth.models import User
import requests
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
import sentry_sdk
from django.http import HttpResponseNotFound
from .forms import * 
from django.db import transaction
from django.http import JsonResponse
import json
from django.utils import timezone




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


def PersonaList(request):
    """
    View to list personas for the authenticated user
    """
    try:
        # Get the session data
        supabase_user_raw = request.session.get('supabase_user')
        
        if not supabase_user_raw:
            print("No supabase_user found in session")
            return redirect('login')
        
        # Parse JSON string to dictionary if it's a string
        if isinstance(supabase_user_raw, str):
            try:
                supabase_user_data = json.loads(supabase_user_raw)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from session: {e}")
                return redirect('login')
        elif isinstance(supabase_user_raw, dict):
            # Already a dictionary
            supabase_user_data = supabase_user_raw
        else:
            print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
            return redirect('login')
        
        # Extract email
        email = supabase_user_data.get('email')
        print(f"Extracted email: {email}")
        
        if not email:
            print("No email found in session data")
            return redirect('login')
        
        # Find the user
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
                return render(request, 'personas.html', {
                    'error_message': 'User not found',
                    'personas': []
                })
        
        # Fetch personas for this user from the main_persona table
        try:
            personas = persona.objects.filter(user=user).order_by('-created_at')
            print(f"Found {personas.count()} personas for user {user}")
        except Exception as e:
            print(f"Error fetching personas: {e}")
            personas = []
        
        # Render the template with personas
        return render(request, 'personas.html', {
            'user': user,
            'personas': personas,
            'error_message': None
        })
        
    except Exception as e:
        print(f"Unexpected error in PersonaList: {e}")
        return render(request, 'personas.html', {
            'error_message': f'An error occurred: {str(e)}',
            'personas': []
        })

def PersonaDetail(request, id):
    """
    View to display detailed information about a specific persona
    Uses the same authentication logic as PersonaList, then filters by ID
    """
    try:
        # First, get all personas using the same logic as PersonaList
        # Get the session data
        supabase_user_raw = request.session.get('supabase_user')
        
        if not supabase_user_raw:
            print("No supabase_user found in session")
            return redirect('login')
        
        # Parse JSON string to dictionary if it's a string
        if isinstance(supabase_user_raw, str):
            try:
                supabase_user_data = json.loads(supabase_user_raw)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from session: {e}")
                return redirect('login')
        elif isinstance(supabase_user_raw, dict):
            # Already a dictionary
            supabase_user_data = supabase_user_raw
        else:
            print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
            return redirect('login')
        
        # Extract email
        email = supabase_user_data.get('email')
        print(f"Extracted email: {email}")
        
        if not email:
            print("No email found in session data")
            return redirect('login')
        
        # Find the user
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
                return render(request, 'detail.html', {
                    'persona': None,
                    'error_message': 'User not found'
                })
        
        # Get all personas for this user, then filter by the specific ID
        try:
            # Import the Persona model (adjust import based on your project structure)
            from main.models import persona  # Change 'main' to your app name if different
            
            # Get all personas for this user
            user_personas = persona.objects.filter(user=user)
            
            # Filter by the specific ID
            persona = user_personas.filter(id=id).first()
            
            if not persona:
                print(f"Persona with ID {id} not found for user {user}")
                return render(request, 'detail.html', {
                    'persona': None,
                    'error_message': 'Persona not found or you do not have permission to view it'
                })
            
            print(f"Found persona: {persona}")
            
        except Exception as e:
            print(f"Error fetching persona: {e}")
            return render(request, 'detail.html', {
                'persona': None,
                'error_message': f'Error accessing persona: {str(e)}'
            })
        
        # Render the detail template
        return render(request, 'detail.html', {
            'persona': persona,
            'error_message': None
        })

    except Exception as e:
        print(f"Unexpected error in PersonaDetail: {e}")
        return render(request, 'detail.html', {
            'persona': None,
            'error_message': f'An error occurred: {str(e)}'
        })


def PersonaDelete(request, id):
    """
    View to delete a specific persona
    Uses the same authentication logic as PersonaList, then deletes by ID
    """
    try:
        # First, authenticate user using the same logic as PersonaList
        supabase_user_raw = request.session.get('supabase_user')
        
        if not supabase_user_raw:
            ##messages.error(request, "Authentication required")
            return redirect('persona-list')
        
        # Parse JSON string to dictionary if it's a string
        if isinstance(supabase_user_raw, str):
            try:
                supabase_user_data = json.loads(supabase_user_raw)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from session: {e}")
               ## messages.error(request, "Session error")
                return redirect('persona-list')
        elif isinstance(supabase_user_raw, dict):
            supabase_user_data = supabase_user_raw
        else:
            print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
          ##  messages.error(request, "Authentication error")
            return redirect('persona-list')
        
        # Extract email
        email = supabase_user_data.get('email')
        
        if not email:
          ##  messages.error(request, "User email not found")
            return redirect('persona-list')
        
        # Find the user
        user = None
        try:
            from login.models import User
            user = User.objects.get(email=email)
        except Exception as e:
            print(f"Error with login.models.User: {e}")
            try:
                from django.contrib.auth.models import User as DjangoUser
                user = DjangoUser.objects.get(email=email)
            except Exception as e2:
                print(f"Error with Django User: {e2}")
             ##   messages.error(request, "User not found")
                return redirect('persona-list')
        
        # Get and delete the persona
        try:
            from main.models import persona  # Adjust import based on your app name
            
            # Get all personas for this user, then filter by the specific ID
            user_personas = persona.objects.filter(user=user)
            persona = user_personas.filter(id=id).first()
            
            if not persona:
            ##    messages.error(request, "Persona not found or you do not have permission to delete it")
                return redirect('persona-list')
            
            # Store persona name for success message
            persona_name = persona.persona_name or f"Persona {persona.id}"
            
            # Delete the persona
            persona.delete()
            
            ##messages.success(request, f"'{persona_name}' has been successfully deleted.")
            print(f"Successfully deleted persona: {persona_name}")
            
        except Exception as e:
            print(f"Error deleting persona: {e}")
           ## messages.error(request, f"Error deleting persona: {str(e)}")
        
        return redirect('persona-list')
        
    except Exception as e:
        print(f"Unexpected error in PersonaDelete: {e}")
       ## messages.error(request, f"An error occurred: {str(e)}")
        return redirect('persona-list')


def PersonaEdit(request, id):
    """
    View to edit a specific persona
    Uses the same authentication logic as PersonaList and PersonaDetail
    """
    try:
        # First, authenticate user using the same logic as other views
        supabase_user_raw = request.session.get('supabase_user')
        
        if not supabase_user_raw:
            print("No supabase_user found in session")
            return redirect('login')
        
        # Parse JSON string to dictionary if it's a string
        if isinstance(supabase_user_raw, str):
            try:
                supabase_user_data = json.loads(supabase_user_raw)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from session: {e}")
                return redirect('login')
        elif isinstance(supabase_user_raw, dict):
            supabase_user_data = supabase_user_raw
        else:
            print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
            return redirect('login')
        
        # Extract email
        email = supabase_user_data.get('email')
        print(f"Extracted email: {email}")
        
        if not email:
            print("No email found in session data")
            return redirect('login')
        
        # Find the user
        user = None
        try:
            from login.models import User
            user = get_object_or_404(User, email=email)
            print(f"Found user in login.models.User: {user}")
        except Exception as e:
            print(f"Error with login.models.User: {e}")
            try:
                from django.contrib.auth.models import User as DjangoUser
                user = get_object_or_404(DjangoUser, email=email)
                print(f"Found user in Django User: {user}")
            except Exception as e2:
                print(f"Error with Django User: {e2}")
                return redirect('persona-list')
        
        # Get the persona to edit
        try:
            user_personas = persona.objects.filter(user=user)
            persona_obj = user_personas.filter(id=id).first()
            
            if not persona_obj:
                print(f"Persona with ID {id} not found for user {user}")
                return redirect('persona-list')
            
            print(f"Found persona to edit: {persona_obj}")
            
        except Exception as e:
            print(f"Error fetching persona: {e}")
            return redirect('persona-list')
        
        # Handle form submission
        if request.method == 'POST':
            form = PersonaEditForm(request.POST, instance=persona_obj)
            
            if form.is_valid():
                try:
                    original_values = {
                        'persona_name': persona_obj.persona_name,
                        # Add other fields you want to track changes for
                    }
                    
                    # Save the updated persona
                    updated_persona = form.save()
                    
                    # Log the edit activity with enhanced debugging
                    try:
                        from log.models import ActivityLog
                        
                        # Get client IP address
                        def get_client_ip(request):
                            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                            if x_forwarded_for:
                                ip = x_forwarded_for.split(',')[0]
                            else:
                                ip = request.META.get('REMOTE_ADDR')
                            return ip
                        
                        # Debug info before creating log
                        print(f"About to create ActivityLog:")
                        print(f"  User: {user} (ID: {user.id})")
                        print(f"  User model: {user.__class__}")
                        print(f"  Persona: {updated_persona} (ID: {updated_persona.id})")
                        print(f"  Action: EDIT")
                        
                        with transaction.atomic():
                            activity_log = ActivityLog.objects.create(
                                user=user,
                                persona=updated_persona,
                                action_type='EDIT',
                                description=f"Edited persona '{updated_persona.persona_name or 'Unnamed'}'",
                                ip_address=get_client_ip(request)
                            )
                        
                        print(f"✅ Activity logged successfully: Edit persona {updated_persona.id}, Log ID: {activity_log.id}")
                        
                    except Exception as log_error:
                        print(f"❌ Failed to log activity: {log_error}")
                        print(f"Error type: {type(log_error).__name__}")
                        
                        # Check if it's a specific database error
                        if hasattr(log_error, 'args'):
                            print(f"Error args: {log_error.args}")
                        
                        # Test minimal ActivityLog creation to isolate issue
                        try:
                            print("Testing minimal log creation...")
                            test_log = ActivityLog.objects.create(
                                user=user,
                                action_type='TEST',
                                description='Test log entry'
                            )
                            print(f"✅ Minimal log created: {test_log.id}")
                            test_log.delete()  # Clean up
                            print("❌ Full log failed but minimal log worked - check persona FK or IP field")
                        except Exception as test_error:
                            print(f"❌ Minimal log creation also failed: {test_error}")
                            print(f"Database connection or User FK issue")
                        
                        import traceback
                        traceback.print_exc()
                    
                    print(f"Successfully updated persona: {updated_persona.persona_name}")
                    return redirect('persona-detail', id=updated_persona.id)
                    
                except Exception as e:
                    print(f"Error saving persona: {e}")
                    import traceback
                    traceback.print_exc()
            
            else:
                print(f"Form validation errors: {form.errors}")
        
        else:
            # GET request
            form = PersonaEditForm(instance=persona_obj)
        
        return render(request, 'persona_edit.html', {
            'form': form,
            'persona': persona_obj,
            'page_title': f'Edit {persona_obj.persona_name or "Persona"}'
        })
    
    except Exception as e:
        print(f"Unexpected error in PersonaEdit view: {e}")
        import traceback
        traceback.print_exc()
        return redirect('persona-list')

def custom_404_view(request, exception):
    sentry_sdk.capture_message(f"404 Not Found: {request.path}", level="info")
    return HttpResponseNotFound("Custom 404 Page")


def create_persona_share_link(request, id):
    """Create a new share link for a persona"""
    try:
        # First, authenticate user using the same logic as PersonaEdit
        supabase_user_raw = request.session.get('supabase_user')
        
        if not supabase_user_raw:
            print("No supabase_user found in session")
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Parse JSON string to dictionary if it's a string
        if isinstance(supabase_user_raw, str):
            try:
                supabase_user_data = json.loads(supabase_user_raw)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from session: {e}")
                return JsonResponse({'error': 'Invalid session data'}, status=401)
        elif isinstance(supabase_user_raw, dict):
            supabase_user_data = supabase_user_raw
        else:
            print(f"Unexpected type for supabase_user: {type(supabase_user_raw)}")
            return JsonResponse({'error': 'Invalid session format'}, status=401)
        
        # Extract email
        email = supabase_user_data.get('email')
        print(f"Extracted email: {email}")
        
        if not email:
            print("No email found in session data")
            return JsonResponse({'error': 'Email not found in session'}, status=401)
        
        # Find the user
        user = None
        try:
            from login.models import User
            user = get_object_or_404(User, email=email)
            print(f"Found user in login.models.User: {user}")
        except Exception as e:
            print(f"Error with login.models.User: {e}")
            try:
                from django.contrib.auth.models import User as DjangoUser
                user = get_object_or_404(DjangoUser, email=email)
                print(f"Found user in Django User: {user}")
            except Exception as e2:
                print(f"Error with Django User: {e2}")
                return JsonResponse({'error': 'User not found'}, status=404)
        
        # Get the persona to share
        try:
            user_personas = persona.objects.filter(user=user)
            persona_obj = user_personas.filter(id=id).first()
            
            if not persona_obj:
                print(f"Persona with ID {persona_id} not found for user {user}")
                return JsonResponse({'error': 'Persona not found or access denied'}, status=404)
            
            print(f"Found persona to share: {persona_obj}")
            
        except Exception as e:
            print(f"Error fetching persona: {e}")
            return JsonResponse({'error': 'Error accessing persona'}, status=500)
        
        # Parse request data
        try:
            data = json.loads(request.body)
            expires_in_hours = data.get('expires_in_hours', 24)
            max_views = data.get('max_views')
            description = data.get('description', '')
            
            # Validate expires_in_hours (max 30 days)
            if expires_in_hours > 720:  # 30 days
                return JsonResponse({'error': 'Maximum expiration time is 30 days'}, status=400)
            
            # Create the share link
            share_link = persona_obj.create_share_link(
                created_by=user,
                expires_in_hours=expires_in_hours,
                max_views=max_views,
                description=description
            )
            
            # Log the share creation activity
            try:
                from log.models import ActivityLog
                
                # Get client IP address
                def get_client_ip(request):
                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    if x_forwarded_for:
                        ip = x_forwarded_for.split(',')[0]
                    else:
                        ip = request.META.get('REMOTE_ADDR')
                    return ip
                
                print(f"About to create ActivityLog for share link creation:")
                print(f"  User: {user} (ID: {user.id})")
                print(f"  Persona: {persona_obj} (ID: {persona_obj.id})")
                print(f"  Action: SHARE")
                
                with transaction.atomic():
                    activity_log = ActivityLog.objects.create(
                        user=user,
                        persona=persona_obj,
                        action_type='SHARE',
                        description=f"Created share link for persona '{persona_obj.persona_name or 'Unnamed'}' (expires in {expires_in_hours}h)",
                        ip_address=get_client_ip(request)
                    )
                
                print(f"✅ Activity logged successfully: Share link created for persona {persona_obj.id}, Log ID: {activity_log.id}")
                
            except Exception as log_error:
                print(f"❌ Failed to log share activity: {log_error}")
                import traceback
                traceback.print_exc()
            
            return JsonResponse({
                'success': True,
                'share_url': share_link.get_share_url(request),
                'expires_at': share_link.expires_at.isoformat(),
                'share_token': share_link.share_token,
                'expires_in_hours': expires_in_hours,
                'max_views': max_views
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Error creating share link: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': 'Failed to create share link'}, status=500)
    
    except Exception as e:
        print(f"Unexpected error in create_persona_share_link view: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)

def shared_persona_detail(request, share_token):
    """
    View a shared persona via a share link.
    The token is used to look up the PersonaShare object.
    """
    try:
        share = get_object_or_404(PersonaShareLink, share_token=share_token)
        
        # Check expiration
        if share.expires_at and share.expires_at < timezone.now():
            raise Http404("This share link has expired.")

        # Check max views
        if share.max_views is not None and share.views_count >= share.max_views:
            raise Http404("This share link has reached the maximum number of views.")

        # Update view count
        share.current_views += 1
        share.save(update_fields=['current_views'])

        persona = share.persona

    except PersonaShareLink.DoesNotExist:
        raise Http404("Shared persona not found.")

    return render(request, "persona_detail_shared.html", {
        "persona": persona,
        "shared": True,   # flag for template to hide edit/delete buttons
        "share": share,
    })

