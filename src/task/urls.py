from django.urls import path

from . import views

app_name = 'task'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('<int:task_id>/toggle/', views.toggle_task, name='toggle'),
    path('<int:task_id>/status/', views.update_task_status, name='status'),
    path('<int:task_id>/today/', views.update_task_today, name='today'),
    path('<int:task_id>/detail/', views.task_detail, name='detail'),
    path('<int:task_id>/edit/', views.edit_task, name='edit'),
    path('<int:task_id>/delete/', views.delete_task, name='delete'),
]
