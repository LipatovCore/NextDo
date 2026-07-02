from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def visible_tasks(self):
        return self.tasks.filter(is_deleted=False)

    @property
    def task_total_count(self):
        return self.visible_tasks.count()

    @property
    def completed_task_count(self):
        return self.visible_tasks.filter(is_completed=True).count()

    @property
    def progress_percent(self):
        total = self.task_total_count
        if not total:
            return 0
        return round(self.completed_task_count * 100 / total)

    def __str__(self):
        return self.title


class Task(models.Model):
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Низкий'),
        (PRIORITY_MEDIUM, 'Обычный'),
        (PRIORITY_HIGH, 'Высокий'),
    ]

    title = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        related_name='tasks',
        null=True,
        blank=True,
    )
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
    )
    deadline = models.DateField(null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def status_label(self):
        return 'Завершена' if self.is_completed else 'Активная'

    @property
    def status_value(self):
        return 'completed' if self.is_completed else 'active'

    @property
    def is_deadline_overdue(self):
        return self.deadline is not None and self.deadline < timezone.localdate()

    @property
    def is_scheduled_overdue(self):
        return (
            self.scheduled_date is not None
            and self.scheduled_date < timezone.localdate()
        )

    @property
    def is_overdue(self):
        return self.is_deadline_overdue or self.is_scheduled_overdue

    def __str__(self):
        return self.title
