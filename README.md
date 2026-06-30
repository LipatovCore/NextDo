# NextDo

NextDo — Django-приложение для управления личными задачами. Пользователь входит в систему, видит только свои задачи, может создавать, завершать и удалять их.

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
