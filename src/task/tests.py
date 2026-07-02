from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from task.models import Project, Task

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
        self.assertIsNone(task.project)
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


class ProjectModelTest(TestCase):
    """Тесты для модели Project и связи с задачами."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_project(self):
        today = timezone.localdate()
        project = Project.objects.create(
            title='Project One',
            user=self.user,
            deadline=today,
        )

        self.assertEqual(str(project), 'Project One')
        self.assertEqual(project.user, self.user)
        self.assertEqual(project.deadline, today)
        self.assertIsNotNone(project.created_at)

    def test_task_project_relation_is_optional(self):
        project = Project.objects.create(
            title='Project One',
            user=self.user,
            deadline=timezone.localdate(),
        )
        task_without_project = Task.objects.create(title='No Project', user=self.user)
        task_with_project = Task.objects.create(
            title='Project Task',
            user=self.user,
            project=project,
        )

        self.assertIsNone(task_without_project.project)
        self.assertEqual(task_with_project.project, project)
        self.assertIn(task_with_project, project.tasks.all())

    def test_project_stats_ignore_soft_deleted_tasks(self):
        project = Project.objects.create(
            title='Project One',
            user=self.user,
            deadline=timezone.localdate(),
        )
        Task.objects.create(title='Active', user=self.user, project=project)
        Task.objects.create(
            title='Done',
            user=self.user,
            project=project,
            is_completed=True,
        )
        Task.objects.create(
            title='Deleted',
            user=self.user,
            project=project,
            is_completed=True,
            is_deleted=True,
        )

        self.assertEqual(project.task_total_count, 2)
        self.assertEqual(project.completed_task_count, 1)
        self.assertEqual(project.progress_percent, 50)


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

    def test_create_task_with_project(self):
        """При создании задачи можно выбрать свой проект."""
        project = Project.objects.create(
            title='Work Project',
            user=self.user,
            deadline=timezone.localdate(),
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url,
            {'title': 'Project Task', 'project': project.id},
        )

        self.assertRedirects(response, self.url)
        task = Task.objects.get(title='Project Task', user=self.user)
        self.assertEqual(task.project, project)

    def test_create_task_rejects_other_user_project(self):
        """POST не может привязать задачу к чужому проекту."""
        other_project = Project.objects.create(
            title='Other Project',
            user=self.other_user,
            deadline=timezone.localdate(),
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url,
            {'title': 'Wrong Project Task', 'project': other_project.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title='Wrong Project Task').exists())

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
        self.assertContains(response, 'Проекты')
        self.assertContains(response, 'Финансы')
        self.assertContains(response, 'Сегодня')
        self.assertContains(response, 'Все задачи')
        self.assertContains(response, 'href="/"')
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, 'href="/projects/"')
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

    def test_task_cards_display_project_in_all_and_today_sections(self):
        """Карточка задачи показывает проект в общих задачах и Сегодня."""
        today = timezone.localdate()
        project = Project.objects.create(
            title='Visible Project',
            user=self.user,
            deadline=today,
        )
        Task.objects.create(
            title='Project Today',
            user=self.user,
            project=project,
            scheduled_date=today,
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertContains(response, 'Visible Project')
        self.assertContains(response, 'Проект:')
        self.assertContains(response, 'Сегодня')

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


class ProjectViewTest(TestCase):
    """Тесты раздела проектов."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.url = reverse('projects')

    def test_project_route_is_top_level_section(self):
        """Раздел проектов смонтирован на /projects/."""
        self.assertEqual(self.url, '/projects/')

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_authenticated_user_access(self):
        """Авторизованный пользователь получает доступ к странице проектов."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/project-list.html')
        self.assertContains(response, 'Проекты')
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, 'href="/projects/"')

    def test_create_project_success_trims_title(self):
        """Создание проекта обрезает лишние пробелы и открывает карточку проекта."""
        today = timezone.localdate()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url,
            {
                'title': '  Work Project  ',
                'deadline': today.isoformat(),
            },
        )

        project = Project.objects.get(title='Work Project', user=self.user)
        self.assertRedirects(response, reverse('project_detail', args=[project.id]))

    def test_create_project_invalid_form(self):
        """Проект без названия не создаётся."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url,
            {
                'title': '   ',
                'deadline': timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(user=self.user).exists())

    def test_display_only_user_projects(self):
        """Пользователь видит только свои проекты."""
        my_project = Project.objects.create(
            title='My Project',
            user=self.user,
            deadline=timezone.localdate(),
        )
        Project.objects.create(
            title='Other Project',
            user=self.other_user,
            deadline=timezone.localdate(),
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertContains(response, my_project.title)
        self.assertNotContains(response, 'Other Project')

    def test_project_card_displays_stats_and_progress(self):
        """Карточка проекта показывает статистику задач и прогресс."""
        project = Project.objects.create(
            title='Stats Project',
            user=self.user,
            deadline=timezone.localdate(),
        )
        Task.objects.create(title='Open', user=self.user, project=project)
        Task.objects.create(
            title='Done',
            user=self.user,
            project=project,
            is_completed=True,
        )
        Task.objects.create(
            title='Deleted',
            user=self.user,
            project=project,
            is_completed=True,
            is_deleted=True,
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertContains(response, 'Всего: 2')
        self.assertContains(response, 'Готово: 1')
        self.assertContains(response, '50%')

    def test_project_detail_displays_project_tasks_only(self):
        """Страница проекта показывает только задачи выбранного проекта."""
        project = Project.objects.create(
            title='Project One',
            user=self.user,
            deadline=timezone.localdate(),
        )
        other_project = Project.objects.create(
            title='Project Two',
            user=self.user,
            deadline=timezone.localdate(),
        )
        project_task = Task.objects.create(
            title='Inside Project',
            user=self.user,
            project=project,
        )
        Task.objects.create(
            title='Other Project Task',
            user=self.user,
            project=other_project,
        )
        Task.objects.create(title='No Project Task', user=self.user)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('project_detail', args=[project.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/project-detail.html')
        self.assertEqual(list(response.context['tasks']), [project_task])
        self.assertContains(response, 'Inside Project')
        self.assertNotContains(response, 'Other Project Task')
        self.assertNotContains(response, 'No Project Task')

    def test_project_detail_updates_project(self):
        """Данные проекта можно редактировать."""
        project = Project.objects.create(
            title='Old Title',
            user=self.user,
            deadline=timezone.localdate(),
        )
        new_deadline = timezone.localdate() + timedelta(days=7)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('project_detail', args=[project.id]),
            {
                'title': 'New Title',
                'deadline': new_deadline.isoformat(),
            },
        )

        self.assertRedirects(response, reverse('project_detail', args=[project.id]))
        project.refresh_from_db()
        self.assertEqual(project.title, 'New Title')
        self.assertEqual(project.deadline, new_deadline)

    def test_project_detail_filter_by_status(self):
        """Фильтры на странице проекта применяются только к задачам проекта."""
        project = Project.objects.create(
            title='Project One',
            user=self.user,
            deadline=timezone.localdate(),
        )
        completed = Task.objects.create(
            title='Completed In Project',
            user=self.user,
            project=project,
            is_completed=True,
        )
        Task.objects.create(title='Active In Project', user=self.user, project=project)
        Task.objects.create(title='Completed Global', user=self.user, is_completed=True)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('project_detail', args=[project.id]),
            {'status': 'completed'},
        )

        self.assertEqual(list(response.context['tasks']), [completed])

    def test_project_ajax_payload_contains_scoped_list_and_stats(self):
        """AJAX-ответ проекта возвращает список проекта и статистику."""
        project = Project.objects.create(
            title='Project One',
            user=self.user,
            deadline=timezone.localdate(),
        )
        Task.objects.create(
            title='Done In Project',
            user=self.user,
            project=project,
            is_completed=True,
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('project_detail', args=[project.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertIn('Done In Project', payload['all_html'])
        self.assertEqual(payload['project_stats']['total'], 1)
        self.assertEqual(payload['project_stats']['completed'], 1)
        self.assertEqual(payload['project_stats']['progress'], 100)

    def test_404_for_other_user_project(self):
        """Пользователь не может открыть чужой проект."""
        other_project = Project.objects.create(
            title='Other Project',
            user=self.other_user,
            deadline=timezone.localdate(),
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('project_detail', args=[other_project.id]))

        self.assertRedirects(response, reverse('home'))


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
        self.assertContains(response, 'Проекты')
        self.assertContains(response, 'Финансы')
        self.assertContains(response, 'Раздел в разработке')
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, 'href="/projects/"')
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
        self.assertContains(response, 'Проекты')
        self.assertContains(response, 'Раздел в разработке')
        self.assertContains(response, 'href="/"')
        self.assertContains(response, 'href="/tasks/"')
        self.assertContains(response, 'href="/projects/"')


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

    def test_edit_endpoint_updates_project(self):
        """Endpoint редактирования сохраняет выбранный проект задачи."""
        project = Project.objects.create(
            title='Ajax Project',
            user=self.user,
            deadline=timezone.localdate(),
        )

        response = self.client.post(
            reverse('task:edit', args=[self.task.id]),
            {
                'title': 'Updated Task',
                'status': 'active',
                'project': project.id,
                'priority': Task.PRIORITY_MEDIUM,
                'deadline': '',
                'scheduled_date': '',
                'description': '',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.project, project)

    def test_edit_endpoint_rejects_other_user_project(self):
        """Endpoint редактирования не принимает чужой проект."""
        other_project = Project.objects.create(
            title='Other Project',
            user=self.other_user,
            deadline=timezone.localdate(),
        )

        response = self.client.post(
            reverse('task:edit', args=[self.task.id]),
            {
                'title': 'Updated Task',
                'status': 'active',
                'project': other_project.id,
                'priority': Task.PRIORITY_MEDIUM,
                'deadline': '',
                'scheduled_date': '',
                'description': '',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.project)

    def test_ajax_task_action_returns_project_scoped_payload(self):
        """AJAX-действие из проекта обновляет список и статистику проекта."""
        project = Project.objects.create(
            title='Scoped Project',
            user=self.user,
            deadline=timezone.localdate(),
        )
        self.task.project = project
        self.task.save(update_fields=['project'])

        response = self.client.post(
            f"{reverse('task:status', args=[self.task.id])}?project={project.id}",
            {'status': 'completed'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('Test Task', payload['all_html'])
        self.assertEqual(payload['project_stats']['total'], 1)
        self.assertEqual(payload['project_stats']['completed'], 1)
        self.assertEqual(payload['project_stats']['progress'], 100)

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
