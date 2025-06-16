from django.urls import path
from .views import *

urlpatterns = [
    path('/login/', login_view, name='login'),
    path('/register/', register_view, name='register'),
    path('/dashboard/', dashboard_view, name='dashboard'),
    path('/logout/', logout_view, name='logout'),
    path('/profile/', user_profile_view, name='profile'),
    path('verify-otp/', verify_otp_view, name='verify_otp')
]
