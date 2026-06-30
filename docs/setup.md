# Установка

## Через Docker Compose

1. Создайте `.env`:

```bash
copy .env.example .env
```

2. Запустите сервисы:

```bash
docker compose up --build
```

Compose поднимает:

- `db` — PostgreSQL 15.
- `web` — миграции, `collectstatic`, Gunicorn.
- `nginx` — порт `80` на хосте.

Адрес приложения: `http://localhost/`.

## Локально без Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/manage.py migrate
python src/manage.py runserver
```

Для локального запуска нужен PostgreSQL и переменные из `.env.example`. Значение `POSTGRES_HOST=db` подходит для Docker Compose; для локального PostgreSQL обычно нужен другой host.

## Первый пользователь

Команды регистрации в проекте не найдено. Для входа создайте пользователя через Django:

```bash
python src/manage.py createsuperuser
```
