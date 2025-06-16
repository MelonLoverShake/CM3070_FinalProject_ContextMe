import requests
import json
from django.conf import settings

class SupabaseAuth:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.headers = {
            'apikey': settings.SUPABASE_ANON_KEY,
            'Content-Type': 'application/json'
        }
    
    def send_otp(self, email):
        """Send OTP to email"""
        endpoint = f"{self.url}/auth/v1/otp"
        data = {
            'email': email,
            'create_user': True  # Set to False if you don't want auto-registration
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            if response.status_code == 200:
                return {'success': True, 'message': 'OTP sent successfully!'}
            else:
                return {'success': False, 'error': response.json().get('msg', 'Failed to send OTP')}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_otp(self, email, token):
        """Verify OTP code"""
        endpoint = f"{self.url}/auth/v1/verify"
        data = {
            'type': 'email',
            'email': email,
            'token': token
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.json().get('msg', 'Invalid OTP')}
        except Exception as e:
            return {'success': False, 'error': str(e)}