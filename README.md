# Car Catalog

Демонстрационный mobile-first сайт-каталог автомобилей для небольшого
автосалона (условный «Premium Cars Warsaw»), который продаёт машины
через Instagram и Telegram. Одна ссылка в bio — и клиент видит все
актуальные автомобили, фильтрует их и записывается на просмотр.

## Стек

- Python 3.14 / Django 6.1
- SQLite (база данных — файл, создаётся автоматически)
- HTML-шаблоны Django + чистый CSS (mobile-first)
- Pillow (работа с загружаемыми фотографиями)

## Запуск проекта локально

1. Клонировать репозиторий и перейти в папку проекта:

   ```
   git clone <адрес-репозитория>
   cd car-catalog
   ```

2. Создать виртуальное окружение и установить зависимости:

   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

   (на Mac/Linux вместо второй строки: `source venv/bin/activate`)

3. Создать базу данных:

   ```
   python manage.py migrate
   ```

4. Создать администратора (для входа в админку):

   ```
   python manage.py createsuperuser
   ```

5. Запустить сервер:

   ```
   python manage.py runserver
   ```

Сайт: http://127.0.0.1:8000/
Админка: http://127.0.0.1:8000/admin/

## Структура проекта

```
car-catalog/
├── config/        # настройки Django (settings.py, urls.py)
├── cars/          # основное приложение: модели, страницы, админка
├── templates/     # HTML-шаблоны
├── static/        # CSS, JS, иконки
├── media/         # загруженные фото автомобилей (не хранится в Git)
├── manage.py
└── requirements.txt
```

## Как мы работаем вдвоём

Смотри `TASKS.md` (список задач) и раздел «Совместная работа» в `CLAUDE.md`.
Коротко: задача → своя ветка → commit → push → Pull Request → merge в main.
