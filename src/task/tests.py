from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from task.models import Task

User = get_user_model()


# =============================================================================
# МОДЕЛЬНЫЕ ТЕСТЫ
# =============================================================================

class TaskModelTest(TestCase):
    """Тесты для модели Task"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_task(self):
        """Тест создания задачи"""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertEqual(str(task), 'Test Task')
        self.assertFalse(task.is_completed)
        self.assertIsNotNone(task.created_at)

    def test_task_user_relation(self):
        """Тест связи с пользователем"""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertEqual(task.user, self.user)
        self.assertIn(task, self.user.tasks.all())

    def test_task_complete(self):
        """Тест завершения задачи"""
        task = Task.objects.create(title='Test Task', user=self.user)
        task.is_completed = True
        task.save()
        self.assertTrue(task.is_completed)

    def test_task_cascade_delete(self):
        """Тест каскадного удаления при удалении пользователя"""
        task = Task.objects.create(title='Test Task', user=self.user)
        task_id = task.id
        self.user.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_task_title_max_length(self):
        """Тест максимальной длины заголовка"""
        task = Task.objects.create(title='Test Task', user=self.user)
        max_length = task._meta.get_field('title').max_length
        self.assertEqual(max_length, 100)

    def test_task_default_values(self):
        """Тест значений по умолчанию"""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertFalse(task.is_completed)

    def test_task_ordering(self):
        """Тест сортировки задач (по умолчанию новые сверху)"""
        task1 = Task.objects.create(title='First Task', user=self.user)
        task2 = Task.objects.create(title='Second Task', user=self.user)
        tasks = list(Task.objects.all())
        self.assertEqual(tasks[0], task2)
        self.assertEqual(tasks[1], task1)


# =============================================================================
# VIEW ТЕСТЫ - СПИСОК ЗАДАЧ
# =============================================================================

class TaskListViewTest(TestCase):
    """Тесты для представления списка задач (task_list)"""

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

    def test_redirect_anonymous_user(self):
        """Анонимный пользователь перенаправляется на страницу входа"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_authenticated_user_access(self):
        """Авторизованный пользователь получает доступ к странице"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/task-list.html')

    def test_display_only_user_tasks(self):
        """Пользователь видит только свои задачи"""
        Task.objects.create(title='My Task', user=self.user)
        Task.objects.create(title='Other Task', user=self.other_user)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        tasks = response.context['tasks']
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().title, 'My Task')

    def test_display_empty_task_list(self):
        """Корректное отображение пустого списка задач"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Нет активных задач')

    def test_create_task_success(self):
        """Успешное создание новой задачи"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url, {'title': 'New Task'})
        self.assertRedirects(response, self.url)
        self.assertTrue(Task.objects.filter(title='New Task', user=self.user).exists())

    def test_create_task_invalid_form(self):
        """Создание задачи с невалидной формой"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url, {'title': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/task-list.html')

    def test_form_displayed_on_get(self):
        """Форма отображается при GET-запросе"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertIn('form', response.context)


# =============================================================================
# VIEW ТЕСТЫ - ПЕРЕКЛЮЧЕНИЕ ЗАДАЧИ
# =============================================================================

class TaskToggleViewTest(TestCase):
    """Тесты для представления переключения задачи (toggle_task)"""

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
        """Анонимный пользователь перенаправляется на страницу входа"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_toggle_task_status(self):
        """Переключение статуса задачи с未完成 на завершено"""
        self.client.login(username='testuser', password='testpass123')
        self.assertFalse(self.task.is_completed)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('task:list'))
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_toggle_back_status(self):
        """Переключение статуса задачи с завершено на未完成"""
        self.task.is_completed = True
        self.task.save()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('task:list'))
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_404_for_other_user_task(self):
        """Возврат 404 при попытке переключить чужую задачу"""
        other_task = Task.objects.create(title='Other Task', user=self.other_user)
        url = reverse('task:toggle', args=[other_task.id])

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


# =============================================================================
# VIEW ТЕСТЫ - УДАЛЕНИЕ ЗАДАЧИ
# =============================================================================

class TaskDeleteViewTest(TestCase):
    """Тесты для представления удаления задачи (delete_task)"""

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
        """Анонимный пользователь перенаправляется на страницу входа"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_delete_task_success(self):
        """Успешное удаление задачи"""
        self.client.login(username='testuser', password='testpass123')
        task_id = self.task.id

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('task:list'))
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_404_for_other_user_task(self):
        """Возврат 404 при попытке удалить чужую задачу"""
        other_task = Task.objects.create(title='Other Task', user=self.other_user)
        url = reverse('task:delete', args=[other_task.id])

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
