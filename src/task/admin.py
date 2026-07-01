from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'is_completed',
        'priority',
        'deadline',
        'scheduled_date',
        'is_deleted',
        'created_at',
    )
    list_filter = ('is_completed', 'priority', 'is_deleted', 'deadline', 'scheduled_date')
    search_fields = ('title', 'description', 'user__username')
