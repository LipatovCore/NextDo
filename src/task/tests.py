from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from task.models import Task

User = get_user_model()


class TaskModelTest(TestCase):
    """Тесты для модели Task."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_task(self):
        """Тест создания задачи."""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertEqual(str(task), 'Test Task')
        self.assertFalse(task.is_completed)
        self.assertEqual(task.priority, Task.PRIORITY_MEDIUM)
        self.assertIsNone(task.deadline)
        self.assertIsNone(task.scheduled_date)
        self.assertEqual(task.description, '')
        self.assertFalse(task.is_deleted)
        self.assertIsNotNone(task.created_at)

    def test_task_user_relation(self):
        """Тест связи с пользователем."""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertEqual(task.user, self.user)
        self.assertIn(task, self.user.tasks.all())

    def test_task_complete(self):
        """Тест завершения задачи."""
        task = Task.objects.create(title='Test Task', user=self.user)
        task.is_completed = True
        task.save()
        self.assertTrue(task.is_completed)
        self.assertEqual(task.status_value, 'completed')
        self.assertEqual(task.status_label, 'Завершена')

    def test_task_cascade_delete(self):
        """Тест каскадного удаления при удалении пользователя."""
        task = Task.objects.create(title='Test Task', user=self.user)
        task_id = task.id
        self.user.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_task_title_max_length(self):
        """Тест максимальной длины заголовка."""
        task = Task.objects.create(title='Test Task', user=self.user)
        max_length = task._meta.get_field('title').max_length
        self.assertEqual(max_length, 100)

    def test_task_default_values(self):
        """Тест значений по умолчанию."""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertFalse(task.is_completed)
        self.assertEqual(task.priority, 'medium')
        self.assertFalse(task.is_deleted)

    def test_task_overdue_flags(self):
        """Просрочка считается только для дат раньше текущего дня."""
        today = timezone.localdate()
        task = Task.objects.create(
            title='Overdue Task',
            user=self.user,
            deadline=today - timedelta(days=1),
            scheduled_date=today,
        )

        self.assertTrue(task.is_deadline_overdue)
        self.assertFalse(task.is_scheduled_overdue)
        self.assertTrue(task.is_overdue)

    def test_task_ordering(self):
        """Тест сортировки задач (по умолчанию новые сверху)."""
        task1 = Task.objects.create(title='First Task', user=self.user)
        task2 = Task.objects.create(title='Second Task', user=self.user)
        tasks = list(Task.objects.all())
        self.assertEqual(tasks[0], task2)
        self.assertEqual(tasks[1], task1)


class TaskListViewTest(TestCase):
    """Тесты для представления списка задач."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.url = reverse('task:list')

    def test_task_list_route_is_tasks_section(self):
        """Экран задач смонтирован в отдельном разделе /tasks/."""
        self.assertEqual(self.url, '/tasks/')

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_authenticated_user_access(self):
        """Авторизованный пользователь получает доступ к странице."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/task-list.html')

    def test_display_only_user_visible_tasks(self):
        """Пользователь видит только свои неудалённые задачи."""
        my_task = Task.objects.create(title='My Task', user=self.user)
        Task.objects.create(title='Deleted Task', user=self.user, is_deleted=True)
        Task.objects.create(title='Other Task', user=self.other_user)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first(), my_task)
        self.assertContains(response, 'My Task')
        self.assertNotContains(response, 'Deleted Task')
        self.assertNotContains(response, 'Other Task')

    def test_display_empty_task_list(self):
        """Корректное отображение пустого списка задач."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Задач пока нет')

    def test_create_task_success_trims_title(self):
        """Успешное создание новой задачи обрезает лишние пробелы."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url, {'title': '  New Task  '})
        self.assertRedirects(response, self.url)
        self.assertTrue(Task.objects.filter(title='New Task', user=self.user).exists())

    def test_create_task_invalid_form(self):
        """Создание задачи с невалидной формой."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url, {'title': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/task-list.html')
        self.assertFalse(Task.objects.filter(user=self.user).exists())

    def test_form_displayed_on_get(self):
        """Форма быстрого создания отображается при GET-запросе."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertIn('quick_form', response.context)

    def test_main_and_secondary_menus_present(self):
        """На странице задач есть навигация и вкладки задач."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertContains(response, 'Главная')
        self.assertContains(response, 'Задачи')
        self.assertContains(response, 'Финансы')
        self.assertContains(response, 'Сегодня')
        self.assertContains(response, 'Все задачи')
        self.assertContains(response, 'href="/"')
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, 'href="/finance/"')
        self.assertNotContains(response, 'Раздел в разработке')

    def test_filter_by_status(self):
        """Фильтр по статусу."""
        Task.objects.create(title='Active Task', user=self.user)
        Task.objects.create(title='Completed Task', user=self.user, is_completed=True)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url, {'status': 'completed'})

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().title, 'Completed Task')

    def test_filter_by_priority(self):
        """Фильтр по приоритету."""
        Task.objects.create(title='Normal Task', user=self.user)
        Task.objects.create(title='High Task', user=self.user, priority=Task.PRIORITY_HIGH)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url, {'priority': 'high'})

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().title, 'High Task')

    def test_filter_by_deadline(self):
        """Фильтр по дедлайну."""
        today = timezone.localdate()
        Task.objects.create(title='Today Deadline', user=self.user, deadline=today)
        Task.objects.create(title='No Deadline', user=self.user)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url, {'deadline': today.isoformat()})

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().title, 'Today Deadline')

    def test_filter_by_scheduled_date(self):
        """Фильтр по дате выполнения."""
        today = timezone.localdate()
        Task.objects.create(title='Scheduled Today', user=self.user, scheduled_date=today)
        Task.objects.create(title='No Schedule', user=self.user)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url, {'scheduled_date': today.isoformat()})

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().title, 'Scheduled Today')

    def test_combined_filters(self):
        """Несколько фильтров работают одновременно."""
        today = timezone.localdate()
        Task.objects.create(
            title='Match',
            user=self.user,
            priority=Task.PRIORITY_HIGH,
            deadline=today,
            scheduled_date=today,
        )
        Task.objects.create(
            title='Wrong Priority',
            user=self.user,
            priority=Task.PRIORITY_LOW,
            deadline=today,
            scheduled_date=today,
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url, {
            'status': 'active',
            'priority': 'high',
            'deadline': today.isoformat(),
            'scheduled_date': today.isoformat(),
        })

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().title, 'Match')

    def test_today_tab_contains_scheduled_today_and_overdue_tasks(self):
        """Вкладка Сегодня собирает задачи на сегодня и просрочки."""
        today = timezone.localdate()
        scheduled_today = Task.objects.create(
            title='Scheduled Today',
            user=self.user,
            scheduled_date=today,
        )
        deadline_overdue = Task.objects.create(
            title='Deadline Overdue',
            user=self.user,
            deadline=today - timedelta(days=1),
        )
        schedule_overdue = Task.objects.create(
            title='Schedule Overdue',
            user=self.user,
            scheduled_date=today - timedelta(days=1),
        )
        future_task = Task.objects.create(
            title='Future Task',
            user=self.user,
            deadline=today + timedelta(days=1),
            scheduled_date=today + timedelta(days=1),
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        today_tasks = list(response.context['today_tasks'])

        self.assertIn(scheduled_today, today_tasks)
        self.assertIn(deadline_overdue, today_tasks)
        self.assertIn(schedule_overdue, today_tasks)
        self.assertNotIn(future_task, today_tasks)

    def test_today_dates_are_not_overdue(self):
        """Сегодняшние даты не считаются просроченными."""
        today = timezone.localdate()
        task = Task.objects.create(
            title='Today Dates',
            user=self.user,
            deadline=today,
            scheduled_date=today,
        )

        self.assertFalse(task.is_deadline_overdue)
        self.assertFalse(task.is_scheduled_overdue)


class HomeViewTest(TestCase):
    """Тесты отдельной главной страницы."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.url = reverse('home')

    def test_home_route_is_root(self):
        """Главная страница смонтирована на корневой маршрут."""
        self.assertEqual(self.url, '/')

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_authenticated_user_access(self):
        """Авторизованный пользователь получает отдельную главную страницу."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/home.html')
        self.assertContains(response, 'Главная')
        self.assertContains(response, 'Задачи')
        self.assertContains(response, 'Финансы')
        self.assertContains(response, 'Раздел в разработке')
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, 'href="/finance/"')
        self.assertNotContains(response, 'Все задачи')
        self.assertNotContains(response, 'Задач пока нет')


class FinanceViewTest(TestCase):
    """Тесты отдельного раздела финансов."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.url = reverse('finance')

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_authenticated_user_access(self):
        """Авторизованный пользователь получает доступ к разделу финансов."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/finance.html')
        self.assertContains(response, 'Финансы')
        self.assertContains(response, 'Раздел в разработке')
        self.assertContains(response, 'href="/"')
        self.assertContains(response, 'href="/tasks/"')


class TaskToggleViewTest(TestCase):
    """Тесты для переключения задачи."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.task = Task.objects.create(title='Test Task', user=self.user)
        self.url = reverse('task:toggle', args=[self.task.id])

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_toggle_task_status(self):
        """Переключение статуса задачи с активной на завершённую."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('task:list'))
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_toggle_back_status(self):
        """Переключение статуса задачи с завершённой на активную."""
        self.task.is_completed = True
        self.task.save()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('task:list'))
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_404_for_other_user_task(self):
        """Возврат 404 при попытке переключить чужую задачу."""
        other_task = Task.objects.create(title='Other Task', user=self.other_user)
        url = reverse('task:toggle', args=[other_task.id])

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)

        self.assertRedirects(response, reverse('home'))


class TaskAjaxEndpointTest(TestCase):
    """Тесты endpoint'ов для JS-enhanced интерфейса."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.task = Task.objects.create(title='Test Task', user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_ajax_create_task_returns_lists(self):
        """AJAX-создание возвращает обновлённые списки."""
        response = self.client.post(
            reverse('task:list'),
            {'title': 'Ajax Task'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertIn('all_html', payload)
        self.assertTrue(Task.objects.filter(title='Ajax Task', user=self.user).exists())

    def test_update_status_endpoint(self):
        """Endpoint быстрого статуса обновляет is_completed."""
        response = self.client.post(
            reverse('task:status', args=[self.task.id]),
            {'status': 'completed'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_today_endpoint_adds_and_removes_today_date(self):
        """Endpoint Сегодня ставит и очищает дату выполнения."""
        today = timezone.localdate()

        add_response = self.client.post(
            reverse('task:today', args=[self.task.id]),
            {'mode': 'add'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(add_response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.scheduled_date, today)

        remove_response = self.client.post(
            reverse('task:today', args=[self.task.id]),
            {'mode': 'remove'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(remove_response.status_code, 200)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.scheduled_date)

    def test_detail_endpoint_returns_card_html(self):
        """Endpoint карточки возвращает HTML формы редактирования."""
        response = self.client.get(
            reverse('task:detail', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('html', response.json())
        self.assertIn('Карточка задачи', response.json()['html'])

    def test_edit_endpoint_updates_all_fields(self):
        """Endpoint редактирования сохраняет основные поля задачи."""
        today = timezone.localdate()
        response = self.client.post(
            reverse('task:edit', args=[self.task.id]),
            {
                'title': 'Updated Task',
                'status': 'completed',
                'priority': Task.PRIORITY_HIGH,
                'deadline': today.isoformat(),
                'scheduled_date': today.isoformat(),
                'description': 'Описание задачи',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')
        self.assertTrue(self.task.is_completed)
        self.assertEqual(self.task.priority, Task.PRIORITY_HIGH)
        self.assertEqual(self.task.deadline, today)
        self.assertEqual(self.task.scheduled_date, today)
        self.assertEqual(self.task.description, 'Описание задачи')

    def test_new_endpoints_do_not_allow_other_user_task(self):
        """Новые endpoint'ы не работают с чужими задачами."""
        other_task = Task.objects.create(title='Other Task', user=self.other_user)
        response = self.client.post(
            reverse('task:status', args=[other_task.id]),
            {'status': 'completed'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 302)
        other_task.refresh_from_db()
        self.assertFalse(other_task.is_completed)


class TaskDeleteViewTest(TestCase):
    """Тесты мягкого удаления задачи."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.task = Task.objects.create(title='Test Task', user=self.user)
        self.url = reverse('task:delete', args=[self.task.id])

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_delete_task_success_is_soft_delete(self):
        """Удаление из UI не удаляет запись физически."""
        self.client.login(username='testuser', password='testpass123')
        task_id = self.task.id

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('task:list'))
        self.assertTrue(Task.objects.filter(id=task_id).exists())
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_deleted)

        list_response = self.client.get(reverse('task:list'))
        self.assertNotContains(list_response, 'Test Task')

    def test_ajax_delete_returns_updated_lists(self):
        """AJAX-удаление возвращает списки без удалённой задачи."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_deleted)
        self.assertNotIn('Test Task', response.json()['all_html'])

    def test_404_for_other_user_task(self):
        """Возврат 404 при попытке удалить чужую задачу."""
        other_task = Task.objects.create(title='Other Task', user=self.other_user)
        url = reverse('task:delete', args=[other_task.id])

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(url)

        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Task.objects.get(id=other_task.id).is_deleted)
