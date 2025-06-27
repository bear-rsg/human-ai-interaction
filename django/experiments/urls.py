from django.urls import path
from . import views, apps

app_name = apps.app_name

urlpatterns = [
    path('', views.experiment_index, name='index'),
    path('experimentinstance/create/', views.experiment_instance_create, name='experimentinstance-create'),
    path('experimentinstance/<int:pk>/', views.experiment_instance_detail, name='experimentinstance-detail'),
    path('experimentinstance/<int:pk>/sethost/', views.experiment_instance_sethost, name='experimentinstance-sethost'),
    path('experimentinstance/<int:pk>/completed/', views.experiment_instance_completed, name='experimentinstance-completed'),
    path('experimentinstance/<int:pk>/feedback/', views.experiment_instance_feedback, name='experimentinstance-feedback'),
    path('experimentinstance/<int:pk>/message/list/', views.experiment_instance_message_list, name='experimentinstancemessage-list'),
    path('experimentinstance/<int:pk>/message/new/user/', views.experiment_instance_message_new_user, name='experimentinstancemessage-new-user'),
    path('experimentinstance/<int:pk>/message/new/ai/', views.experiment_instance_message_new_ai, name='experimentinstancemessage-new-ai'),
    path('experimentinstance/exportdata/', views.experiment_instance_exportdata, name='experimentinstance-exportdata'),
]
