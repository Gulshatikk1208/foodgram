#!/bin/sh

/app/wait-for-it.sh db 5432

python manage.py makemigrations --noinput
python manage.py migrate --noinput

python manage.py load_ingredients

python manage.py collectstatic --noinput
cp -r /app/collected_static/. /backend_static/static/

exec gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8050 --timeout 120
