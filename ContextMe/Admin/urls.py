from django.urls import path
from . import views

app_name = 'admin_app'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('admin-dashboard/', views.Admin_Dashboard, name="Admin_Dashboard"),
    path('user-personas/', views.user_personas, name="user_personas_list"),
]
