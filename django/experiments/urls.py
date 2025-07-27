from django.urls import path
from . import views, apps

app_name = apps.app_name

urlpatterns = [
    path('', views.experiment_index, name='index'),
    path('experimentinstance/createorjoin/', views.experiment_instance_create_or_join, name='experimentinstance-createorjoin'),
    path('experimentinstance/<int:pk>/', views.experiment_instance_detail, name='experimentinstance-detail'),
    path('experimentinstance/<int:pk>/setresponder/', views.experiment_instance_setresponder, name='experimentinstance-setresponder'),
    path('experimentinstance/<int:pk>/survey/', views.experiment_instance_survey, name='experimentinstance-survey'),
    path('experimentinstance/<int:pk>/message/list/', views.experiment_instance_message_list, name='experimentinstancemessage-list'),
    path('experimentinstance/<int:pk>/message/new/user/', views.experiment_instance_message_new_user, name='experimentinstancemessage-new-user'),
    path('experimentinstance/<int:pk>/message/new/ai/', views.experiment_instance_message_new_ai, name='experimentinstancemessage-new-ai'),
    path('experimentinstance/exportdata/', views.experiment_instance_exportdata, name='experimentinstance-exportdata'),
]
