# Обзор проекта

NextDo — Django-приложение для личного списка задач.

## Возможности

- Вход и выход через стандартную аутентификацию Django.
- Просмотр списка задач текущего пользователя.
- Создание задачи с названием до 100 символов.
- Переключение статуса задачи: активная или завершенная.
- Удаление задачи.
- Скрытие и показ завершенных задач на странице списка.

## Стек

- Python 3.13 в Docker-образе.
- Django 6.0.3.
- PostgreSQL 15 в Docker Compose.
- SQLite для тестов.
- Gunicorn для запуска Django в контейнере.
- nginx для входящего HTTP и статических файлов.

## Ключевые файлы

- `src/config/settings.py` — настройки Django, БД, статика, auth redirects.
- `src/config/urls.py` — маршруты admin, login, logout, tasks.
- `src/task/models.py` — модель `Task`.
- `src/task/views.py` — обработчики списка, переключения и удаления задач.
- `src/task/tests.py` — тесты модели и views.
- `docker-compose.yml` — запуск PostgreSQL, web и nginx.
- `.env.example` — пример окружения.
