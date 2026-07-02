# NextDo

NextDo — Django-приложение для управления личными задачами и проектами. Пользователь входит в систему, видит только свои неудалённые задачи и проекты, может создавать, планировать, фильтровать, завершать и мягко удалять задачи.

Главная страница `/` — отдельный защищённый раздел приложения. Задачи доступны на `/tasks/`, проекты — на `/projects/`, а раздел «Финансы» — на `/finance/`.

## Быстрый старт

1. Создайте `.env` на основе `.env.example`.
2. Запустите проект через Docker Compose:

```bash
docker compose up --build
```

Приложение будет доступно через nginx на `http://localhost/`.

## Локальная разработка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/manage.py migrate
python src/manage.py runserver
```

Тесты:

```bash
python src/manage.py test task
```

## Документация

- [Обзор проекта](docs/overview.md)
- [Архитектура](docs/architecture.md)
- [Установка](docs/setup.md)
- [Разработка](docs/development.md)
- [Тестирование](docs/testing.md)
- [Стиль кода](docs/code-style.md)
- [Деплой](docs/deployment.md)
- [Окружение](docs/environment.md)
- [Диагностика](docs/troubleshooting.md)

Инструкция для Codex: [AGENTS.md](AGENTS.md).
