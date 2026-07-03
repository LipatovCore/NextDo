from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ProjectForm, TaskDetailsForm, TaskQuickCreateForm
from .models import Project, Task


def redirect_to_task(request, exception=None):
    return redirect('home')


def _is_fetch_request(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _visible_projects(user):
    return Project.objects.filter(user=user, is_deleted=False)


def _visible_tasks(user):
    return Task.objects.select_related('project').filter(user=user, is_deleted=False)


def _project_context_from_request(request):
    project_id = request.GET.get('project', '').strip()
    if not project_id:
        return None

    try:
        project_id = int(project_id)
    except ValueError:
        return None

    return _visible_projects(request.user).filter(id=project_id).first()


def _context_redirect(request):
    project = _project_context_from_request(request)
    if project:
        return redirect('project_detail', project_id=project.id)
    return redirect('task:list')


def _project_stats(project):
    tasks = project.tasks.filter(is_deleted=False)
    total = tasks.count()
    completed = tasks.filter(is_completed=True).count()
    progress = round(completed * 100 / total) if total else 0
    return {
        'total': total,
        'completed': completed,
        'progress': progress,
    }


def _projects_with_stats(user):
    projects = list(
        _visible_projects(user).annotate(
            stats_total=Count(
                'tasks',
                filter=Q(tasks__is_deleted=False),
            ),
            stats_completed=Count(
                'tasks',
                filter=Q(tasks__is_deleted=False, tasks__is_completed=True),
            ),
        )
    )
    for project in projects:
        project.stats_progress = (
            round(project.stats_completed * 100 / project.stats_total)
            if project.stats_total
            else 0
        )
    return projects


def _parse_date(value):
    if not value:
        return ''
    try:
        return date.fromisoformat(value)
    except ValueError:
        return ''


def _task_filters(query_params):
    status = query_params.get('status', '').strip()
    priority = query_params.get('priority', '').strip()
    deadline = _parse_date(query_params.get('deadline', '').strip())
    scheduled_date = _parse_date(query_params.get('scheduled_date', '').strip())

    if status not in {'active', 'completed'}:
        status = ''

    priority_values = {value for value, _ in Task.PRIORITY_CHOICES}
    if priority not in priority_values:
        priority = ''

    return {
        'status': status,
        'priority': priority,
        'deadline': deadline,
        'scheduled_date': scheduled_date,
    }


def _filters_are_active(filters):
    return any(filters.values())


def _apply_task_filters(tasks, filters):
    if filters['status'] == 'active':
        tasks = tasks.filter(is_completed=False)
    elif filters['status'] == 'completed':
        tasks = tasks.filter(is_completed=True)

    if filters['priority']:
        tasks = tasks.filter(priority=filters['priority'])

    if filters['deadline']:
        tasks = tasks.filter(deadline=filters['deadline'])

    if filters['scheduled_date']:
        tasks = tasks.filter(scheduled_date=filters['scheduled_date'])

    return tasks


def _today_tasks(tasks, today):
    return tasks.filter(
        Q(scheduled_date__lte=today) | Q(deadline__lt=today)
    ).distinct()


def _task_context(request, quick_form=None, project=None):
    today = timezone.localdate()
    base_tasks = _visible_tasks(request.user)
    if project is not None:
        base_tasks = base_tasks.filter(project=project)

    filters = _task_filters(request.GET)
    filtered_tasks = _apply_task_filters(base_tasks, filters)
    today_tasks = _today_tasks(base_tasks, today)

    if quick_form is None:
        quick_form_kwargs = {'user': request.user}
        if project is not None:
            quick_form_kwargs['initial'] = {'project': project}
        quick_form = TaskQuickCreateForm(**quick_form_kwargs)

    quick_create_action = reverse('task:list')
    filter_action = reverse('task:list')
    if project is not None:
        quick_create_action = f'{quick_create_action}?project={project.id}'
        filter_action = reverse('project_detail', kwargs={'project_id': project.id})

    return {
        'quick_form': quick_form,
        'quick_create_action': quick_create_action,
        'filter_action': filter_action,
        'tasks': filtered_tasks,
        'today_tasks': today_tasks,
        'all_tasks_count': base_tasks.count(),
        'filtered_tasks_count': filtered_tasks.count(),
        'today_tasks_count': today_tasks.count(),
        'filters': filters,
        'filters_active': _filters_are_active(filters),
        'priority_choices': Task.PRIORITY_CHOICES,
        'project_context': project,
        'task_action_query': f'?project={project.id}' if project is not None else '',
        'today': today,
    }


def _render_task_list(request, context, list_kind):
    tasks = context['today_tasks'] if list_kind == 'today' else context['tasks']
    return render_to_string(
        'task/partials/_task_list.html',
        {
            **context,
            'list_kind': list_kind,
            'list_tasks': tasks,
        },
        request=request,
    )


def _lists_payload(request, message='', project=None):
    if project is None:
        project = _project_context_from_request(request)

    context = _task_context(request, project=project)
    list_kind = 'project' if project is not None else 'all'
    payload = {
        'ok': True,
        'message': message,
        'all_html': _render_task_list(request, context, list_kind),
        'today_html': _render_task_list(request, context, 'today'),
        'counts': {
            'all': context['filtered_tasks_count'],
            'today': context['today_tasks_count'],
        },
    }
    if project is not None:
        payload['project_stats'] = _project_stats(project)
    return payload


def _json_lists_response(request, message='', project=None):
    return JsonResponse(_lists_payload(request, message=message, project=project))


def _first_form_error(form):
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return 'Проверьте данные формы.'


def _json_form_error(form, status=400):
    return JsonResponse(
        {
            'ok': False,
            'error': _first_form_error(form),
            'errors': form.errors,
        },
        status=status,
    )


def _json_error(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status)


@login_required
def task_list(request):
    """Вывод списка задач и создание новой."""
    if request.method == 'POST':
        form = TaskQuickCreateForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            if _is_fetch_request(request):
                return _json_lists_response(request, 'Задача создана.')
            return _context_redirect(request)

        if _is_fetch_request(request):
            return _json_form_error(form)

        context = _task_context(request, quick_form=form)
        return render(request, 'task/task-list.html', context)

    context = _task_context(request)
    if _is_fetch_request(request):
        return _json_lists_response(request)

    return render(request, 'task/task-list.html', context)


@login_required
def project_list(request):
    """Список проектов и создание нового проекта."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()

    context = {
        'project_form': form,
        'projects': _projects_with_stats(request.user),
        'projects_count': _visible_projects(request.user).count(),
    }
    return render(request, 'task/project-list.html', context)


@login_required
def project_detail(request, project_id):
    """Редактирование проекта и список его задач."""
    project = get_object_or_404(_visible_projects(request.user), id=project_id)

    if request.method == 'POST':
        project_form = ProjectForm(request.POST, instance=project)
        if project_form.is_valid():
            project_form.save()
            return redirect('project_detail', project_id=project.id)
    else:
        project_form = ProjectForm(instance=project)

    if _is_fetch_request(request) and request.method == 'GET':
        return _json_lists_response(request, project=project)

    task_context = _task_context(request, project=project)
    context = {
        **task_context,
        'project': project,
        'project_form': project_form,
        'project_stats': _project_stats(project),
    }
    return render(request, 'task/project-detail.html', context)


@login_required
@require_POST
def delete_project(request, project_id):
    """Мягкое удаление проекта без удаления связанных задач."""
    project = get_object_or_404(_visible_projects(request.user), id=project_id)
    project.is_deleted = True
    project.save(update_fields=['is_deleted'])
    return redirect('projects')


@login_required
def toggle_task(request, task_id):
    """Переключение статуса задачи."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    task.is_completed = not task.is_completed
    task.save(update_fields=['is_completed'])

    if _is_fetch_request(request):
        return _json_lists_response(request, 'Статус обновлён.')
    return _context_redirect(request)


@login_required
@require_POST
def update_task_status(request, task_id):
    """Быстрое изменение статуса из мини-карточки."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    status = request.POST.get('status')

    if status not in {'active', 'completed'}:
        if _is_fetch_request(request):
            return _json_error('Неизвестный статус задачи.')
        return _context_redirect(request)

    task.is_completed = status == 'completed'
    task.save(update_fields=['is_completed'])

    if _is_fetch_request(request):
        return _json_lists_response(request, 'Статус обновлён.')
    return _context_redirect(request)


@login_required
@require_POST
def update_task_today(request, task_id):
    """Добавление задачи в список на сегодня или снятие даты выполнения."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    mode = request.POST.get('mode', 'toggle')
    today = timezone.localdate()

    if mode == 'remove' or (mode == 'toggle' and task.scheduled_date == today):
        task.scheduled_date = None
        message = 'Задача убрана из списка на сегодня.'
    else:
        task.scheduled_date = today
        message = 'Задача добавлена в список на сегодня.'

    task.save(update_fields=['scheduled_date'])

    if _is_fetch_request(request):
        return _json_lists_response(request, message)
    return _context_redirect(request)


@login_required
def task_detail(request, task_id):
    """Полная карточка задачи."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    project_context = _project_context_from_request(request)
    context = {
        'task': task,
        'detail_form': TaskDetailsForm(instance=task, user=request.user),
        'project_context': project_context,
        'task_action_query': f'?project={project_context.id}' if project_context else '',
        'today': timezone.localdate(),
    }
    html = render_to_string(
        'task/partials/_task_detail.html',
        context,
        request=request,
    )

    if _is_fetch_request(request):
        return JsonResponse({'ok': True, 'html': html})
    return render(request, 'task/partials/_task_detail.html', context)


@login_required
@require_POST
def edit_task(request, task_id):
    """Сохранение полной карточки задачи."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    form = TaskDetailsForm(request.POST, instance=task, user=request.user)

    if form.is_valid():
        form.save()
        if _is_fetch_request(request):
            return _json_lists_response(request, 'Задача сохранена.')
        return _context_redirect(request)

    if _is_fetch_request(request):
        project_context = _project_context_from_request(request)
        html = render_to_string(
            'task/partials/_task_detail.html',
            {
                'task': task,
                'detail_form': form,
                'project_context': project_context,
                'task_action_query': f'?project={project_context.id}' if project_context else '',
                'today': timezone.localdate(),
            },
            request=request,
        )
        return JsonResponse(
            {
                'ok': False,
                'error': _first_form_error(form),
                'html': html,
            },
            status=400,
        )

    context = _task_context(request)
    return render(request, 'task/task-list.html', context)


@login_required
def delete_task(request, task_id):
    """Мягкое удаление задачи."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    task.is_deleted = True
    task.save(update_fields=['is_deleted'])

    if _is_fetch_request(request):
        return _json_lists_response(request, 'Задача удалена из списка.')
    return _context_redirect(request)
