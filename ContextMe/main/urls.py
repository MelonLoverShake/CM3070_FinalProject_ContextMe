from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path('personas/user/<uuid:user_id>/', UserPersonasList.as_view(), name='user-personas-list'),
    path('personas/<uuid:id>/', UserPersonaDetail.as_view(), name='persona-detail'),
    path('personas/list', views.PersonaList, name='persona-list'),
    path('personas/detail/<uuid:id>/', views.PersonaDetail, name='persona-detail_web'),
    path('personas/<uuid:id>/delete/', views.PersonaDelete, name='persona_delete'),

]
