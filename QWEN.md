# NextDo — Контекст проекта

## Обзор проекта

**NextDo** — это простой менеджер задач, разработанный как персональная система для фиксации задач, уменьшения умственного беспорядка и облегчения начала выполнения задач.

### Технологии
- **Фреймворк:** Django 6.0.3
- **Язык:** Python
- **База данных:** SQLite (по умолчанию)
- **Структура:** Стандартный проект Django с конфигурацией в `src/config/`

### Архитектура
```
NextDo/
├── src/
│   ├── manage.py          # Точка входа для команд Django
│   └── config/            # Конфигурация проекта
│       ├── settings.py    # Настройки Django
│       ├── urls.py        # Маршрутизация URL
│       ├── wsgi.py        # WSGI-конфигурация
│       └── asgi.py        # ASGI-конфигурация
├── requirements.txt       # Зависимости Python
└── .venv/                 # Виртуальное окружение (игнорируется)
```

## Сборка и запуск

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск сервера разработки
```bash
cd src
python manage.py runserver
```

### Миграции базы данных
```bash
python manage.py migrate          # Применить миграции
python manage.py makemigrations   # Создать новые миграции
```

### Создание суперпользователя
```bash
python manage.py createsuperuser
```

### Запуск тестов
```bash
python manage.py test
```

## Конфигурация

### Ключевые настройки (src/config/settings.py)
- **DEBUG:** `True` (режим разработки)
- **DATABASES:** SQLite (`db.sqlite3`)
- **STATIC_URL:** `'static/'`
- **LANGUAGE_CODE:** `'en-us'`
- **TIME_ZONE:** `'UTC'`

### Приложения
Проект использует стандартные приложения Django:
- `django.contrib.admin` — админ-панель
- `django.contrib.auth` — аутентификация
- `django.contrib.contenttypes` — система типов контента
- `django.contrib.sessions` — сессии
- `django.contrib.messages` — сообщения
- `django.contrib.staticfiles` — статические файлы

## Соглашения разработки

### Структура кода
- Следовать стандартным соглашениям Django
- Модули приложений размещаются на уровне `src/`
- Конфигурация вынесена в `src/config/`

### Безопасность
- `SECRET_KEY` хранится в `settings.py` (для разработки)
- `DEBUG = True` только для разработки
- Для production необходимо:
  - Установить `DEBUG = False`
  - Настроить `ALLOWED_HOSTS`
  - Вынести секретный ключ в переменные окружения

### Git
- Виртуальное окружение (`.venv/`) игнорируется
- Файлы базы данных (`db.sqlite3*`) игнорируются
- Byte-compiled файлы (`__pycache__/`) игнорируются

## Примечания

- Проект находится на ранней стадии разработки (базовая конфигурация Django)
- Пользовательские приложения ещё не созданы
- Для расширения функциональности необходимо создать Django-приложения через `python manage.py startapp <app_name>`
