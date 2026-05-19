# Этап 1 дизайн-плана: анализ и подготовка

Дата аудита: 2026-05-19

## 1. Маршруты

### Текущие маршруты

В текущем Django-приложении зафиксированы следующие пользовательские и служебные маршруты:

- `/login/` - вход через стандартный `LoginView` Django, шаблон `registration/login.html`.
- `/logout/` - выход через стандартный `LogoutView` Django, шаблон `registration/logout.html`.
- `/tasks/` - список задач и создание новой задачи, routes из `task.urls`.
- `/tasks/<task_id>/toggle/` - переключение статуса задачи.
- `/tasks/<task_id>/delete/` - удаление задачи.
- `/admin/` - стандартная административная панель Django.
- `handler404` - неизвестные URL перенаправляются на `/tasks/` через `task.views.redirect_to_task`.

Важно для следующих этапов: `toggle` и `delete` сейчас являются отдельными GET-доступными URL, хотя меняют данные. Их нужно заменить на POST + CSRF на этапе переработки поведения задач.

### Будущие маршруты из upgrade-plan

В `docs/project-upgrade-plan.md` запланированы следующие будущие разделы:

- `/dashboard/` - стартовый dashboard после входа.
- `/projects/` - список и создание проектов.
- `/finance/` - финансовый overview.
- `/finance/expenses/` - список расходов.
- `/finance/expenses/new/` - создание расхода.
- `/finance/incomes/` - список доходов.
- `/finance/incomes/new/` - создание дохода.
- `/finance/items/` - справочник позиций.
- `/finance/reports/` - статистика и отчеты.

Эти маршруты пока не реализованы и должны учитываться при проектировании будущего app shell и навигации.

## 2. Шаблоны и inline-ресурсы

### Инвентаризация шаблонов

Текущие пользовательские шаблоны:

- `src/templates/base.html` - общий HTML layout, header, user menu, logout form, базовый `<style>`, блоки `extra_style`, `content`, `extra_script`.
- `src/templates/task/task-list.html` - страница задач, форма создания, счетчики, переключатель видимости завершенных задач, список задач, empty state, inline JS.
- `src/templates/registration/login.html` - страница входа, auth panel, поля логина и пароля, error message, system status.
- `src/templates/registration/logout.html` - страница выхода, auth panel, ссылки повторного входа и перехода к задачам, system status.

### Inline CSS

Весь текущий пользовательский CSS находится внутри шаблонов:

- `base.html` содержит основной `<style>` с reset, body, header, logo, user menu, logout button, main content и responsive-правилами.
- Дочерние шаблоны добавляют CSS через `{% block extra_style %}`.
- В `task-list.html`, `login.html` и `logout.html` стили страниц описаны прямо в шаблонах.

Отдельного общего static CSS для пользовательского интерфейса пока нет.

### Inline JS

Inline JavaScript найден в `task-list.html`.

Он отвечает за:

- подсчет активных и завершенных задач на клиенте;
- скрытие и показ завершенных задач;
- обновление текста кнопки `Показать завершённые` / `Скрыть завершённые`;
- показ filtered empty state, когда активных задач нет.

Других inline JS-обработчиков вида `onclick=` или `onchange=` в шаблонах не найдено.

## 3. Повторяющиеся UI-паттерны

В текущих шаблонах повторяются следующие визуальные и структурные паттерны:

- terminal/cyberpunk shell: темный фон, зеленый акцент `#00ff88`, monospace, uppercase, letter spacing, glow/shadow.
- Panels: `task-panel`, `login-panel`, `logout-panel` с темным фоном, рамкой, border radius и свечением.
- Scan-line decoration: псевдоэлемент `::before` и `@keyframes scan` повторяются в task/auth панелях.
- System status: декоративная строка статуса с мигающей точкой используется на task, login и logout страницах.
- Buttons and links: прозрачные кнопки с рамкой, uppercase, letter spacing, hover glow; варианты primary-like, secondary и danger-hover.
- Form groups: label + input, темный фон полей, зеленая рамка, focus glow.
- Task rows: checkbox-like ссылка, текст задачи, row actions, completed state.
- Empty state: центрированный текст с приглушенным зеленым цветом.
- Responsive breakpoints: правила для `768px` и `480px` повторяются на уровне layout, task page и auth pages.

Эти паттерны нужно заменить на спокойную SaaS/dashboard-систему на следующих этапах, но текущий аудит фиксирует их как исходное состояние.

## 4. Первые кандидаты на вынос в static CSS

Первым шагом редизайна стоит вынести в общий static CSS следующие группы стилей:

- reset и базовую типографику;
- общий layout shell;
- навигацию и user menu;
- кнопки: primary, secondary, ghost, danger, icon;
- формы: labels, inputs, password/search/date/amount fields, field errors;
- panels/cards/content sections;
- task list, task row, task actions, task status;
- auth panels;
- empty, status, alert и toast states;
- responsive-правила для основных breakpoint'ов.

Для нового дизайна эти группы лучше оформить как базовую дизайн-систему, а не переносить текущий terminal/cyberpunk CSS один к одному.

## 5. Viewport'ы для проверки

Базовые ширины для ручной и визуальной проверки:

- `1440px` - широкий desktop.
- `1366px` - типовой laptop/desktop.
- `1024px` - tablet landscape / узкий desktop.
- `768px` - tablet portrait.
- `390px` - mobile.

На следующих этапах эти viewport'ы должны использоваться для проверки app shell, списков, форм, таблиц, action buttons и длинного текста.

## 6. Название сущности товаров/объектов

Для интерфейса временно утверждено рабочее название: `Позиции`.

Это название используется как нейтральное для будущего справочника `/finance/items/` и строк расходов. Оно не ограничивает модель только товарами или только объектами и может быть уточнено отдельным продуктовым решением позже.

На этапе 1 это решение фиксируется только в документации. Пользовательский интерфейс и код не меняются.

## 7. Статус design.pen

`docs/design.pen` не используется как обязательный источник дизайна для этапа 1.

Через Pencil MCP файл проверен 2026-05-19: в документе есть один frame 800x600 с белой заливкой, без компонентов, переменных и полноценного макета. Это совпадает с ранее зафиксированным выводом в `docs/project-upgrade-plan.md`.

Следующие этапы должны опираться на `docs/design-specification.md`, `docs/project-upgrade-plan.md` и фактическое состояние Django-шаблонов. `design.pen` можно использовать позже только после наполнения реальными макетами или компонентами.

## 8. Итог этапа 1

Чеклист этапа 1 закрыт:

- текущие маршруты зафиксированы;
- будущие маршруты из upgrade-plan зафиксированы;
- текущие шаблоны проверены;
- inline CSS и inline JS зафиксированы;
- повторяющиеся UI-паттерны описаны;
- первые кандидаты на вынос в общий static CSS определены;
- viewport'ы для проверки зафиксированы;
- временное название сущности `Позиции` зафиксировано;
- `design.pen` проверен и не считается обязательным источником дизайна.

Этап 1 является документационным. Код приложения, шаблоны, маршруты, стили и поведение не изменялись.
