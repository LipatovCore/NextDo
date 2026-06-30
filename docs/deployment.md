# Деплой

## Docker Compose

`docker-compose.yml` описывает три сервиса:

- `db` — PostgreSQL 15 с volume `postgres_data`.
- `web` — сборка из локального `Dockerfile`.
- `nginx` — `nginx:alpine`, порт `80:80`.

Команда запуска:

```bash
docker compose up --build
```

## Web container

В `docker-compose.yml` контейнер `web` выполняет:

```bash
python manage.py migrate &&
python manage.py collectstatic --noinput &&
gunicorn --bind 0.0.0.0:8000 config.wsgi
```

`Dockerfile` использует:

- `python:3.13-slim`;
- `WORKDIR /app`;
- установку `gcc`;
- `pip install -r requirements.txt`;
- рабочую директорию `/app/src`;
- Gunicorn на `0.0.0.0:8000`.

## nginx

`nginx.conf`:

- слушает порт `80`;
- отдает `/static/` из `/app/staticfiles/`;
- проксирует остальные запросы на `http://web:8000`;
- передает заголовки `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

## Что проверить перед production

- `SECRET_KEY` задан через секретное значение, не из примера.
- `DEBUG=False`.
- `ALLOWED_HOSTS` содержит реальные домены.
- `POSTGRES_PASSWORD` заменен.
- nginx-конфиг соответствует домену и TLS-схеме. TLS в репозитории не настроен.
