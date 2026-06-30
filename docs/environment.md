# Окружение

Переменные перечислены в `.env.example` и читаются в `src/config/settings.py`.

## Django

| Переменная | Назначение | Пример |
| --- | --- | --- |
| `SECRET_KEY` | секрет Django | `your-secret-key-here` |
| `DEBUG` | режим отладки | `True` |
| `ALLOWED_HOSTS` | список разрешенных hosts через запятую | `localhost,127.0.0.1` |

## PostgreSQL

| Переменная | Назначение | Пример |
| --- | --- | --- |
| `POSTGRES_DB` | имя базы | `nextdo` |
| `POSTGRES_USER` | пользователь БД | `nextdo` |
| `POSTGRES_PASSWORD` | пароль БД | `your-postgres-password-here` |
| `POSTGRES_HOST` | host БД | `db` |
| `POSTGRES_PORT` | порт БД | `5432` |

## Docker Compose

`docker-compose.yml` дополнительно задает:

```text
DATABASE_URL=postgres://nextdo:${POSTGRES_PASSWORD:-nextdo_password}@db:5432/nextdo
```

В текущем `src/config/settings.py` `DATABASE_URL` не читается; подключение к PostgreSQL идет через `POSTGRES_*`.

## Секреты

- Не коммитьте `.env`.
- Не переносите реальные пароли в документацию.
- Для production замените все значения из `.env.example`.
