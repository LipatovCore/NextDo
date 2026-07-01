# Диагностика

## `SECRET_KEY` не задан

`src/config/settings.py` вызывает `config('SECRET_KEY')` без значения по умолчанию. Создайте `.env` на основе `.env.example` и задайте `SECRET_KEY`.

## Ошибка подключения к PostgreSQL локально

По умолчанию host базы — `db`, что подходит для Docker Compose. При запуске без Docker задайте `POSTGRES_HOST` под локальный PostgreSQL.

## Нельзя войти в приложение

В проекте не найдена регистрация пользователей. Создайте пользователя:

```bash
python src/manage.py createsuperuser
```

Затем войдите через `/login/`.

## Статика не отображается в Docker

Проверьте, что `web` выполнил:

```bash
python manage.py collectstatic --noinput
```

В Compose статика пишется в volume `static_volume`, nginx отдает ее из `/app/staticfiles/`.

## Тесты используют не PostgreSQL

Это ожидаемое поведение. При наличии `test` в `sys.argv` настройки переключаются на SQLite `BASE_DIR / 'test_db.sqlite3'`.

## Фильтр статуса не показывает ожидаемые задачи

Проверьте параметр `status` в адресной строке или сбросьте фильтры на странице задач. Допустимые значения: `active`, `completed` или пустое значение для всех неудалённых задач.
