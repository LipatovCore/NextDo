# Архитектура

## Компоненты

- `config` — Django-проект: настройки, корневые маршруты, WSGI/ASGI.
- `task` — Django-приложение задач.
- `templates` — серверные HTML-шаблоны с CSS и небольшим JavaScript в `task-list.html`.
- `db` — PostgreSQL 15 в Docker Compose.
- `web` — Django + Gunicorn.
- `nginx` — reverse proxy на `web:8000` и отдача `/static/`.

## Модель данных

`Task` хранит:

- `title` — `CharField(max_length=100)`.
- `user` — внешний ключ на `settings.AUTH_USER_MODEL`.
- `is_completed` — флаг завершения, по умолчанию `False`.
- `created_at` — дата создания.

Сортировка по умолчанию: новые задачи сверху через `ordering = ['-created_at']`.

## Маршруты

- `/admin/` — Django admin.
- `/login/` — стандартный `LoginView` с шаблоном `registration/login.html`.
- `/logout/` — стандартный `LogoutView` с шаблоном `registration/logout.html`.
- `/tasks/` — список и создание задач.
- `/tasks/<task_id>/toggle/` — переключение статуса задачи.
- `/tasks/<task_id>/delete/` — удаление задачи.

## Поток запроса

1. nginx принимает HTTP-запрос.
2. nginx проксирует приложение на `web:8000`.
3. Gunicorn передает запрос в `config.wsgi`.
4. Django выбирает маршрут в `config.urls` или `task.urls`.
5. `task.views` работает только с задачами текущего пользователя.

## Ограничения

- Регистрация пользователей в коде не найдена; пользователей можно создавать через admin, management command или shell Django.
- API в формате JSON/REST не найден.
- Фоновые задачи и внешние интеграции не найдены.
