from django import forms

from .models import Task


class TaskQuickCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "task-field task-title-input",
                    "placeholder": "Новая задача",
                    "autocomplete": "off",
                }
            )
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Введите название задачи.")
        return title


class TaskDetailsForm(forms.ModelForm):
    STATUS_CHOICES = [
        ("active", "Активная"),
        ("completed", "Завершена"),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Статус",
        widget=forms.Select(attrs={"class": "task-field"}),
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "status",
            "priority",
            "deadline",
            "scheduled_date",
            "description",
        ]
        labels = {
            "title": "Название",
            "priority": "Приоритет",
            "deadline": "Дедлайн",
            "scheduled_date": "Дата выполнения",
            "description": "Описание",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "task-field",
                    "autocomplete": "off",
                }
            ),
            "priority": forms.Select(attrs={"class": "task-field"}),
            "deadline": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "task-field", "type": "date"},
            ),
            "scheduled_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "task-field", "type": "date"},
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "task-field task-textarea",
                    "rows": 5,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["status"].initial = self.instance.status_value

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Введите название задачи.")
        return title

    def save(self, commit=True):
        task = super().save(commit=False)
        task.is_completed = self.cleaned_data["status"] == "completed"
        if commit:
            task.save()
        return task
