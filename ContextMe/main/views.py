from rest_framework import generics, permissions
from .models import persona
from .serializers import PersonaSerializer
from django.contrib.auth.models import User
import requests
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
import sentry_sdk
from django.http import HttpResponseNotFound
from .forms import * 



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
              #  messages.error(request, 'User not found')
                return redirect('persona-list')
        
        # Get the persona to edit
        try:
            # Get all personas for this user, then filter by the specific ID
            user_personas = persona.objects.filter(user=user)
            persona_obj = user_personas.filter(id=id).first()
            
            if not persona_obj:
                print(f"Persona with ID {id} not found for user {user}")
            #    messages.error(request, 'Persona not found or you do not have permission to edit it')
                return redirect('persona-list')
            
            print(f"Found persona to edit: {persona_obj}")
            
        except Exception as e:
            print(f"Error fetching persona: {e}")
         #   messages.error(request, f'Error accessing persona: {str(e)}')
            return redirect('persona-list')
        
        # Handle form submission
        if request.method == 'POST':
            form = PersonaEditForm(request.POST, instance=persona_obj)
            
            if form.is_valid():
                try:
                    # Save the updated persona
                    updated_persona = form.save()
                    
                    print(f"Successfully updated persona: {updated_persona.persona_name}")
                 #   messages.success(request, f"'{updated_persona.persona_name or 'Persona'}' has been successfully updated.")
                    
                    # Redirect to detail view or persona list
                    return redirect('persona-detail', id=updated_persona.id)
                    
                except Exception as e:
                    print(f"Error saving persona: {e}")
                #    messages.error(request, f'Error saving persona: {str(e)}')
            
            else:
                print(f"Form validation errors: {form.errors}")
              #  messages.error(request, 'Please correct the errors below.')
        
        else:
            # GET request - show the form with current data
            form = PersonaEditForm(instance=persona_obj)
        
        # Render the edit template
        return render(request, 'persona_edit.html', {
            'form': form,
            'persona': persona_obj,
            'page_title': f'Edit {persona_obj.persona_name or "Persona"}'
        })

    except Exception as e:
        print(f"Unexpected error in PersonaEdit: {e}")
        #messages.error(request, f'An error occurred: {str(e)}')
        return redirect('persona-list')


def custom_404_view(request, exception):
    sentry_sdk.capture_message(f"404 Not Found: {request.path}", level="info")
    return HttpResponseNotFound("Custom 404 Page")
