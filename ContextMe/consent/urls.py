from django.urls import path
from . import views

urlpatterns = [
    path('consent/', views.consent_view, name='consent'),
]