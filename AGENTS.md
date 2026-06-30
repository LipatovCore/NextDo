# AGENTS.md

## Project Summary

NextDo — небольшое Django-приложение для личного списка задач. Пользователь должен войти в систему, после чего может просматривать только свои задачи, создавать новые, переключать статус выполнения и удалять задачи.

## Tech Stack

- Python 3.13 в Dockerfile.
- Django 6.0.3.
- PostgreSQL 15 для обычного запуска через Docker Compose.
- SQLite для тестов, если команда содержит `test`.
- Gunicorn 25.1.0 как WSGI-сервер.
- nginx alpine как reverse proxy и сервер статических файлов.
- python-decouple для чтения переменных окружения.

## Project Structure

- `src/manage.py` — CLI Django.
- `src/config/` — настройки, URLConf, WSGI/ASGI.
- `src/task/` — приложение задач: модель, формы, views, urls, тесты, миграции.
- `src/templates/` — Django-шаблоны интерфейса и страниц входа/выхода.
- `requirements.txt` — Python-зависимости.
- `Dockerfile` — образ веб-приложения.
- `docker-compose.yml` — сервисы `db`, `web`, `nginx`.
- `nginx.conf` — проксирование на `web:8000` и отдача `/static/`.
- `.env.example` — пример переменных окружения.
- `docs/` — проектная документация.
- `.codex/skills/docs/SKILL.md` — локальный навык Codex для генерации документации.

## Setup

Скопируйте пример окружения:

```bash
copy .env.example .env
```

Запуск через Docker Compose:

```bash
docker compose up --build
```

Локальная установка без Docker:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/manage.py migrate
python src/manage.py runserver
```

Для локального PostgreSQL задайте переменные из `.env.example`. Без Docker настройки по умолчанию ожидают PostgreSQL на хосте `db`, поэтому обычно нужно изменить `POSTGRES_HOST`.

## Development Commands

```bash
python src/manage.py runserver
python src/manage.py makemigrations
python src/manage.py migrate
python src/manage.py createsuperuser
python src/manage.py collectstatic --noinput
docker compose up --build
```

## Testing

```bash
python src/manage.py test task
```

Тесты находятся в `src/task/tests.py` и покрывают модель `Task`, список задач, переключение статуса и удаление. При тестовом запуске `src/config/settings.py` переключает базу данных на SQLite.

## Code Style

- Используйте стиль существующего Django-кода.
- Линтер, форматтер и конфиг типизации не найдены.
- Строки в Python-коде сейчас смешивают одинарные и двойные кавычки; при изменениях придерживайтесь локального стиля файла.
- UI-стили находятся прямо в шаблонах через блок `extra_style`.

## Architecture Notes

- Главный маршрут задач подключен как `path('tasks/', include('task.urls'))`.
- Аутентификация использует стандартные Django views для login/logout.
- Все task views защищены `login_required`.
- Данные задач изолированы по пользователю через фильтр `Task.objects.filter(user=request.user)`.
- `Task` связан с `settings.AUTH_USER_MODEL` через `ForeignKey` и удаляется каскадно вместе с пользователем.
- 404 обработчик перенаправляет на `/tasks/`.

## Documentation Map

- `README.md` — краткая точка входа.
- `docs/overview.md` — назначение и стек.
- `docs/architecture.md` — компоненты и поток запроса.
- `docs/setup.md` — установка.
- `docs/development.md` — рабочие команды.
- `docs/testing.md` — тестовый контур.
- `docs/code-style.md` — стиль и найденные соглашения.
- `docs/deployment.md` — Docker/nginx/Gunicorn.
- `docs/environment.md` — переменные окружения.
- `docs/troubleshooting.md` — частые проблемы.

## Rules for Codex

- Перед изменениями изучи релевантные файлы проекта.
- Не выдумывай архитектуру, команды или зависимости.
- Не меняй публичные API без необходимости.
- Не удаляй код без понимания его назначения.
- После изменений обновляй связанную документацию.
- Если добавлена новая логика, добавь или обнови тесты.
- Если команда тестирования неизвестна, укажи это явно.
- Если в проекте есть линтер или форматтер, используй существующие правила.
- Если есть несколько приложений или пакетов, документируй каждый отдельно.
- Перед изменениями модели читай `src/task/models.py`, миграции и связанные тесты.
- Перед изменениями маршрутов читай `src/config/urls.py`, `src/task/urls.py` и view-тесты.
- Перед изменениями шаблонов читай `src/templates/base.html` и конкретный шаблон страницы.
- Перед изменениями запуска или деплоя читай `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `.env.example` и `src/config/settings.py`.

## Do Not

- Не добавлять неиспользуемые зависимости.
- Не переписывать архитектуру без явного запроса.
- Не создавать длинную документацию ради объема.
- Не дублировать информацию между файлами.
- Не указывать команды, которых нет в проекте.
- Не хранить секреты, токены и пароли в документации.
- Не изменять production-конфиги без явного запроса.
- Не коммитить `.env`, базу данных, `staticfiles`, `.venv`, `__pycache__` и `*.pyc`.
