from django.urls import path
from . import views

urlpatterns = [
    path('activity-log/', views.activity_log_list, name='activity_log_List'),
    path('download/txt/', views.download_activity_log_txt, name='download_txt'),
    path('download/pdf/', views.download_activity_log_pdf, name='download_pdf'),
]
