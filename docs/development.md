# Разработка

## Основные команды

Запуск dev-сервера:

```bash
python src/manage.py runserver
```

Миграции:

```bash
python src/manage.py makemigrations
python src/manage.py migrate
```

Создание администратора:

```bash
python src/manage.py createsuperuser
```

Сбор статических файлов:

```bash
python src/manage.py collectstatic --noinput
```

Запуск контейнеров:

```bash
docker compose up --build
```

## Где менять код

- Модель задачи: `src/task/models.py`.
- HTML/CSS списка задач: `src/templates/task/task-list.html`.
- Вход/выход: `src/templates/registration/`.
- Маршруты приложения задач: `src/task/urls.py`.
- Корневые маршруты: `src/config/urls.py`.
- Настройки окружения и БД: `src/config/settings.py`.

## Перед изменениями

- Для модели читайте `src/task/models.py`, миграции и `src/task/tests.py`.
- Для views читайте `src/task/views.py`, `src/task/urls.py` и view-тесты.
- Для шаблонов читайте `src/templates/base.html` и конкретный шаблон.
- Для Docker/nginx читайте `Dockerfile`, `docker-compose.yml`, `nginx.conf`.
