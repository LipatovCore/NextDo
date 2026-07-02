from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path(
        '',
        login_required(TemplateView.as_view(template_name='home/home.html')),
        name='home',
    ),
    path('tasks/', include('task.urls')),
    path(
        'finance/',
        login_required(TemplateView.as_view(template_name='finance/finance.html')),
        name='finance',
    ),
]

handler404 = 'task.views.redirect_to_task'
