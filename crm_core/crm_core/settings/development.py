from .base import *
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = True

ALLOWED_HOSTS = ['*', 'crm-core', 'nginx:8000']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'odynn_platform'),   # default DB name
        'USER': os.getenv('POSTGRES_USER', 'admin'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'Pass123'),
        'HOST': os.getenv('POSTGRES_HOST', 'postgres'),      # use service name in Docker
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}


#Throttling
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apiservice.authentication.ClientAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'apiservice.throttling.CustomerRateThrottle',
        # 'apiservice.throttling.UserCrawlerRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'customer': '60/minute',
        # 'user_crawler': '5/minute',
    }
}

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = None
CELERY_RESULT_EXPIRES = 300
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
enable_utc = False

# Other dev-specific settings can be added here (e.g., email-backend console)
