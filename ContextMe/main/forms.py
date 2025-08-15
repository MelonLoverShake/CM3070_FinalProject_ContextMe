from django import forms
from .models import persona

class PersonaEditForm(forms.ModelForm):
    class Meta:
        model = persona
        fields = [
            'persona_name',
            'username', 
            'pronouns',
            'context',
            'bio',
            'avatar_url',
            'email',
            'phone',
            'visibility',
            'is_active'
        ]
        
        widgets = {
            'persona_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter persona name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'pronouns': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., they/them, she/her, he/him'
            }),
            'context': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief context or role'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about this persona...'
            }),
            'avatar_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/avatar.jpg'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'persona@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'visibility': forms.Select(
                choices=[
                    ('private', 'Private'),
                    ('public', 'Public'),
                    ('friends', 'Friends Only')
                ],
                attrs={'class': 'form-control'}
            ),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'persona_name': 'Persona Name',
            'username': 'Username',
            'pronouns': 'Pronouns',
            'context': 'Context/Role',
            'bio': 'Biography',
            'avatar_url': 'Avatar URL',
            'email': 'Email',
            'phone': 'Phone Number',
            'visibility': 'Visibility',
            'is_active': 'Active Status'
        }
        
        help_texts = {
            'persona_name': 'The display name for this persona',
            'username': 'A unique username (optional)',
            'pronouns': 'Preferred pronouns for this persona',
            'context': 'Brief description of the persona\'s role or context',
            'bio': 'Detailed description of the persona',
            'avatar_url': 'URL to an avatar image',
            'email': 'Contact email for this persona',
            'phone': 'Contact phone number',
            'visibility': 'Who can see this persona',
            'is_active': 'Whether this persona is currently active'
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username is unique for this user (excluding current instance)
            existing = persona.objects.filter(
                username=username,
                user=self.instance.user
            ).exclude(id=self.instance.id)
            
            if existing.exists():
                raise forms.ValidationError("This username is already taken by another of your personas.")
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Basic email validation is handled by EmailField, 
            # but we can add custom validation here if needed
            pass
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove common formatting characters
            cleaned_phone = ''.join(filter(str.isdigit, phone.replace('+', '+')))
            # You can add more phone validation logic here
        return phone