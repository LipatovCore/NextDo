from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm


@login_required
def task_list(request):
    """Вывод списка задач и создание новой"""
    tasks = Task.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return redirect('task:list')
    else:
        form = TaskForm()
    
    return render(request, 'task/task-list.html', {
        'tasks': tasks,
        'form': form
    })


@login_required
def toggle_task(request, task_id):
    """Переключение статуса задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('task:list')


@login_required
def delete_task(request, task_id):
    """Удаление задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('task:list')
