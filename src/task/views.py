from datetime import date

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .forms import TaskDetailsForm, TaskQuickCreateForm
from .models import Task


def redirect_to_task(request, exception=None):
    return redirect('home')


def _is_fetch_request(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _visible_tasks(user):
    return Task.objects.filter(user=user, is_deleted=False)


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


def _task_context(request, quick_form=None):
    today = timezone.localdate()
    base_tasks = _visible_tasks(request.user)
    filters = _task_filters(request.GET)
    filtered_tasks = _apply_task_filters(base_tasks, filters)
    today_tasks = _today_tasks(base_tasks, today)

    return {
        'quick_form': quick_form or TaskQuickCreateForm(),
        'tasks': filtered_tasks,
        'today_tasks': today_tasks,
        'all_tasks_count': base_tasks.count(),
        'filtered_tasks_count': filtered_tasks.count(),
        'today_tasks_count': today_tasks.count(),
        'filters': filters,
        'filters_active': _filters_are_active(filters),
        'priority_choices': Task.PRIORITY_CHOICES,
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


def _lists_payload(request, message=''):
    context = _task_context(request)
    return {
        'ok': True,
        'message': message,
        'all_html': _render_task_list(request, context, 'all'),
        'today_html': _render_task_list(request, context, 'today'),
        'counts': {
            'all': context['filtered_tasks_count'],
            'today': context['today_tasks_count'],
        },
    }


def _json_lists_response(request, message=''):
    return JsonResponse(_lists_payload(request, message=message))


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
        form = TaskQuickCreateForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            if _is_fetch_request(request):
                return _json_lists_response(request, 'Задача создана.')
            return redirect('task:list')

        if _is_fetch_request(request):
            return _json_form_error(form)

        context = _task_context(request, quick_form=form)
        return render(request, 'task/task-list.html', context)

    context = _task_context(request)
    if _is_fetch_request(request):
        return _json_lists_response(request)

    return render(request, 'task/task-list.html', context)


@login_required
def toggle_task(request, task_id):
    """Переключение статуса задачи."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    task.is_completed = not task.is_completed
    task.save(update_fields=['is_completed'])

    if _is_fetch_request(request):
        return _json_lists_response(request, 'Статус обновлён.')
    return redirect('task:list')


@login_required
@require_POST
def update_task_status(request, task_id):
    """Быстрое изменение статуса из мини-карточки."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    status = request.POST.get('status')

    if status not in {'active', 'completed'}:
        if _is_fetch_request(request):
            return _json_error('Неизвестный статус задачи.')
        return redirect('task:list')

    task.is_completed = status == 'completed'
    task.save(update_fields=['is_completed'])

    if _is_fetch_request(request):
        return _json_lists_response(request, 'Статус обновлён.')
    return redirect('task:list')


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
    return redirect('task:list')


@login_required
def task_detail(request, task_id):
    """Полная карточка задачи."""
    task = get_object_or_404(_visible_tasks(request.user), id=task_id)
    context = {
        'task': task,
        'detail_form': TaskDetailsForm(instance=task),
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
    form = TaskDetailsForm(request.POST, instance=task)

    if form.is_valid():
        form.save()
        if _is_fetch_request(request):
            return _json_lists_response(request, 'Задача сохранена.')
        return redirect('task:list')

    if _is_fetch_request(request):
        html = render_to_string(
            'task/partials/_task_detail.html',
            {
                'task': task,
                'detail_form': form,
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
    return redirect('task:list')
