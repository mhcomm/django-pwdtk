import os
BASE_DIR = os.path.realpath(os.path.dirname(__file__))
TOP_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '%(levelname)s %(name)s %(message)s',
            }
        },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'INFO',
            },
        'django.db.backends.schema': {
            'level': 'WARNING',
            },
    },
}

log_cfg = os.path.join(TOP_DIR, 'log_settings.py')
if os.path.isfile(log_cfg):
    from log_settings import LOGGING  # noqa: F401

del log_cfg
del BASE_DIR
del TOP_DIR
