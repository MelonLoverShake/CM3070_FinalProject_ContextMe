from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('/login/', login_view, name='login'),
    path('/register/', register_view, name='register'),
    path('/dashboard/', dashboard_view, name='dashboard'),
    path('/logout/', logout_view, name='logout'),
    path('/profile/', user_profile_view, name='profile'),
    path('/verify-otp/', verify_otp_view, name='verify_otp'),
    path('/change-password/', views.change_password_view, name='change_password'),
    path('/download/', views.user_download_view, name='user_download'),
    path('/download/txt/', views.download_user_data_txt, name='download_user_txt'),
    path('/download/pdf/', views.download_user_data_pdf, name='download_user_pdf'),
    path('/settings/', views.settings_account_view, name="settings_account"),
    path('/settings/delete-account/', views.delete_account_form_view, name='delete_account'),
]
