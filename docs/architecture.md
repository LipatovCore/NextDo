# Архитектура

## Компоненты

- `config` — Django-проект: настройки, корневые маршруты, WSGI/ASGI.
- `task` — Django-приложение задач.
- `templates` — серверные HTML-шаблоны с CSS, partial-шаблонами задач и небольшим JavaScript в `task-list.html`.
- `db` — PostgreSQL 15 в Docker Compose.
- `web` — Django + Gunicorn.
- `nginx` — reverse proxy на `web:8000` и отдача `/static/`.

## Модель данных

`Task` хранит:

- `title` — `CharField(max_length=100)`.
- `user` — внешний ключ на `settings.AUTH_USER_MODEL`.
- `is_completed` — флаг завершения, по умолчанию `False`.
- `priority` — приоритет `low`, `medium` или `high`; по умолчанию `medium`.
- `deadline` — дедлайн задачи, может быть пустым.
- `scheduled_date` — дата выполнения/планирования, может быть пустой.
- `description` — описание задачи.
- `is_deleted` — флаг мягкого удаления, по умолчанию `False`.
- `created_at` — дата создания.

Сортировка по умолчанию: новые задачи сверху через `ordering = ['-created_at']`.

Обычные списки задач строятся только по `user=request.user` и `is_deleted=False`. Вкладка «Сегодня» показывает задачи с `scheduled_date` на текущий день, а также задачи, у которых `deadline` или `scheduled_date` строго раньше текущей даты.

## Маршруты

- `/admin/` — Django admin.
- `/login/` — стандартный `LoginView` с шаблоном `registration/login.html`.
- `/logout/` — стандартный `LogoutView` с шаблоном `registration/logout.html`.
- `/` — отдельная главная страница.
- `/tasks/` — список и создание задач.
- `/finance/` — отдельный защищённый раздел финансов.
- `/tasks/<task_id>/toggle/` — переключение статуса задачи.
- `/tasks/<task_id>/status/` — установка статуса из мини-карточки.
- `/tasks/<task_id>/today/` — добавление задачи в список на сегодня или очистка даты выполнения.
- `/tasks/<task_id>/detail/` — HTML полной карточки задачи.
- `/tasks/<task_id>/edit/` — сохранение полной карточки задачи.
- `/tasks/<task_id>/delete/` — мягкое удаление задачи через `is_deleted=True`.

## Поток запроса

1. nginx принимает HTTP-запрос.
2. nginx проксирует приложение на `web:8000`.
3. Gunicorn передает запрос в `config.wsgi`.
4. Django выбирает маршрут в `config.urls` или `task.urls`.
5. `task.views` работает только с задачами текущего пользователя.

Страница `/` рендерится отдельным серверным Django-шаблоном главной страницы. Страница `/tasks/` рендерит рабочий раздел задач. Для быстрого создания, фильтров, изменения статуса, даты «Сегодня», карточки и мягкого удаления используется vanilla JS с fetch-запросами к Django views. Эти views возвращают JSON с обновлёнными HTML partials, а без fetch-запроса продолжают работать через обычный render/redirect.

## Ограничения

- Регистрация пользователей в коде не найдена; пользователей можно создавать через admin, management command или shell Django.
- Отдельный REST API не выделен; JSON-ответы используются только для улучшения серверного интерфейса `/tasks/`.
- Фоновые задачи и внешние интеграции не найдены.
