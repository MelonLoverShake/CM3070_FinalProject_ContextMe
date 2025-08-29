import sys
import os
import uuid
from django.contrib.auth.hashers import make_password

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ContextMe.settings")
django.setup()

from Admin.models import Admin_users

# Create admin user
if not Admin_users.objects.filter(username="Jessia_Ruby").exists():
    hashed_password = make_password("AdminJessia")
    Admin_users.objects.create(
        admin_id=uuid.UUID("3d6d6702-62f5-4515-a831-72c6c1312551"),  
        username="Jessia_Ruby",
        password=hashed_password,
        admin_level=1 
    )
    print("Admin created ✅")
else:
    print("Admin already exists ❌")