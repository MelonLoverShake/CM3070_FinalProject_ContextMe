from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path('personas/user/<uuid:user_id>/', UserPersonasList.as_view(), name='user-personas-list'),
    path('personas/<uuid:id>/', UserPersonaDetail.as_view(), name='persona-detail'),
]
