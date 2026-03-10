from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'task'

urlpatterns = [
    path('', login_required(views.index), name='list'),
]
