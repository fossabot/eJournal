"""
Django settings for VLE project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
import os
from collections import OrderedDict
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASELINK = os.environ['BASELINK']

STATIC_URL = '/static/'
# NOTE: Public media directory (not used as such, should probably be renamed.)
MEDIA_URL = 'media/'

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']


# Email settings
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_PORT = 587


# LTI settings
LTI_SECRET = os.environ['LTI_SECRET']
LTI_KEY = os.environ['LTI_KEY']
ROLES = OrderedDict({'Teacher': 'instructor', 'TA': 'teachingassistant', 'Student': 'learner'})
LTI_ROLES = OrderedDict({'instructor': 'Teacher', 'teachingassistant': 'TA', 'learner': 'Student'})


# Celery settings
CELERY_BROKER_URL = os.environ['BROKER_URL']
CELERY_RESULT_BACKEND = 'django-db://{}:{}@{}:{}/{}'.format(
    os.environ['DATABASE_USER'],
    os.environ['DATABASE_PASSWORD'],
    os.environ['DATABASE_HOST'],
    os.environ['DATABASE_PORT'],
    os.environ['DATABASE_NAME']
)
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'

# Read for webserver, r + w for django
FILE_UPLOAD_PERMISSIONS = 0o644

GROUP_API = 'https://api.datanose.nl/Groups/{}'

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'VLE.apps.VLEConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_results',
    'django_celery_beat',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'VLE.utils.throttle.GDPRThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'gdpr': '3/day',
    },
}

AUTH_USER_MODEL = "VLE.User"

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'id',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'VLE.utils.error_handling.ErrorMiddleware',
]

ROOT_URLCONF = 'VLE.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (os.path.join(BASE_DIR, 'templates/email_templates/'),),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'VLE.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = False
