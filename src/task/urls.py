from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'task'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('<int:task_id>/toggle/', views.toggle_task, name='toggle'),
    path('<int:task_id>/delete/', views.delete_task, name='delete'),
]
