"""
Django settings for VLE project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

from VLE.settings.base import *

ENVIRONMENT = 'PRODUCTION'

MEDIA_ROOT = os.environ['MEDIA_ROOT']
STATIC_ROOT = os.environ['STATIC_ROOT']
BACKUP_DIR = os.environ['BACKUP_DIR']

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([a-zA-Z0-9_\-]+\.)?ejournal\.app$',
)

MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE

ALLOWED_HOSTS = ['.ejournal.app', '.canvas.uva.nl']

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# NOTE: CSP takes presedence over X_FRAME if both are supported
X_FRAME_OPTIONS = 'DENY'
CSP_DEFAULT_SRC = ("'self'", 'canvas.uva.nl')
SECURE_BROWSER_XSS_FILTER = True

DEBUG = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': os.environ['DATABASE_PORT'],
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        },
    },
    'handlers': {
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '{}/django_info.log'.format(os.environ["LOG_DIR"]),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'req_warning_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '{}/django_request_warning.log'.format(os.environ["LOG_DIR"]),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '{}/django_error.log'.format(os.environ["LOG_DIR"]),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['info_file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['req_warning_file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
