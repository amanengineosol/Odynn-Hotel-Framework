from .base import *
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = True

ALLOWED_HOSTS = ['*', 'crm-core:8000','http://k8s-stage-crmcorei-801bd72af5-1729448934.us-east-1.elb.amazonaws.com/api/sendRequest/hotel/']

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
       
    ],
    'DEFAULT_THROTTLE_RATES': {
        'customer': '60/minute',
        
    }
}

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_RESULT_EXPIRES = 300
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
enable_utc = True
