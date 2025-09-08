# crm_core/settings/production.py
from .base import *
import os

DEBUG = False

# Set to your production domain(s)
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Secure secret key from environment variable or secrets manager in prod
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-secret-key')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'odynn_platform'),
        'USER': os.environ.get('POSTGRES_USER', 'admin'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'Pass@123'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', "amqp://admin:Pass123@localhost:5672")
CELERY_RESULT_BACKEND = None
CELERY_RESULT_EXPIRES = 300
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
enable_utc = False

# Additional production settings like SSL, security middleware configs, etc.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configure email settings from environment, cache, logging, etc.
