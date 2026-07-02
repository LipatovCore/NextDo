from django import forms

from .models import Project, Task


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "deadline"]
        labels = {
            "title": "Название",
            "deadline": "Дедлайн",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "task-field",
                    "autocomplete": "off",
                }
            ),
            "deadline": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "task-field", "type": "date"},
            ),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Введите название проекта.")
        return title


class TaskQuickCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "project"]
        labels = {
            "project": "Проект",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "task-field task-title-input",
                    "placeholder": "Новая задача",
                    "autocomplete": "off",
                }
            ),
            "project": forms.Select(attrs={"class": "task-field"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False
        self.fields["project"].empty_label = "Без проекта"
        if user is not None:
            self.fields["project"].queryset = Project.objects.filter(user=user)
        else:
            self.fields["project"].queryset = Project.objects.none()

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
            "project",
            "priority",
            "deadline",
            "scheduled_date",
            "description",
        ]
        labels = {
            "title": "Название",
            "project": "Проект",
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
            "project": forms.Select(attrs={"class": "task-field"}),
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False
        self.fields["project"].empty_label = "Без проекта"
        if user is not None:
            self.fields["project"].queryset = Project.objects.filter(user=user)
        else:
            self.fields["project"].queryset = Project.objects.none()
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
