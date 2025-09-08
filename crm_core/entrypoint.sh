#!/bin/sh
python manage.py migrate
python manage.py collectstatic

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='sunny.kumar@engineosol.com').exists():
    User.objects.create_superuser('sunny.kumar@engineosol.com', 'Pass@123')
"

exec gunicorn crm_core.wsgi:application --bind 0.0.0.0:8000 --workers 3
