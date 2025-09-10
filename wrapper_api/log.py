import logging
import watchtower
import sys

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name} {process:d} {thread:d} {message}', 'style': '{'},
        'simple': {'format': '{levelname} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        # 'cloudwatch': {
        #     'class': 'watchtower.CloudWatchLogHandler',
        #     'log_group': 'hotel-platform-service-logs',
        #     'stream_name': 'app',
        #     'level': 'INFO',
        # },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'fastapi': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}