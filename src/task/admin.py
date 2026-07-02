from django.contrib import admin

from .models import Project, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'deadline',
        'created_at',
    )
    list_filter = ('deadline', 'created_at')
    search_fields = ('title', 'user__username')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'project',
        'is_completed',
        'priority',
        'deadline',
        'scheduled_date',
        'is_deleted',
        'created_at',
    )
    list_filter = ('is_completed', 'priority', 'is_deleted', 'project', 'deadline', 'scheduled_date')
    search_fields = ('title', 'description', 'project__title', 'user__username')
