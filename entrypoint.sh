#!/bin/bash

# Выполняем миграции
poetry run python manage.py migrate

# Собираем статические файлы
poetry run python manage.py collectstatic --noinput

# Запускаем Gunicorn
exec "$@"
