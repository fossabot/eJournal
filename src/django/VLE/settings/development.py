"""
Django settings for VLE project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

SECRET_KEY = '@a4c3cpgfe0@8s!be=23d5+3e30vyj7!q%tolqpewafp^-@=br'

from VLE.settings.base import *

LTI_SECRET = '4339900ae5861f3086861ea492772864'
LTI_KEY = '0cd500938a8e7414ccd31899710c98ce'

BASELINK = 'http://localhost:8080'
CORS_ORIGIN_ALLOW_ALL = True

MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'VLE.db'),
    }
}
DEBUG = True
