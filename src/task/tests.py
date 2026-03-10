from django.test import TestCase
from django.contrib.auth import get_user_model
from task.models import Task

User = get_user_model()


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
