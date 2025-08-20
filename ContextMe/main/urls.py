from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path('personas/user/<uuid:user_id>/', UserPersonasList.as_view(), name='user-personas-list'),
    path('personas/<uuid:id>/', UserPersonaDetail.as_view(), name='persona-detail'),
    path('personas/list', views.PersonaList, name='persona-list'),
    path('personas/detail/<uuid:id>/', views.PersonaDetail, name='persona-detail_web'),
    path('personas/<uuid:id>/delete/', views.PersonaDelete, name='persona_delete'),
    path('edit/<uuid:id>/', views.PersonaEdit, name='persona-edit'),
    path('persona/<uuid:id>/create-share/', views.create_persona_share_link, name='create_persona_share_link'),
    path('persona/shared/<str:share_token>/', views.shared_persona_detail, name='shared-persona-detail'),
    path('persona-links/', views.PersonaLinksView, name='persona-links'),

]
