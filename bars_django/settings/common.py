"""
Django settings for bars_django project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
"""
Two things are wrong with Django's default `SECRET_KEY` system:

1. It is not random but pseudo-random
2. It saves and displays the SECRET_KEY in `settings.py`

This snippet
1. uses `SystemRandom()` instead to generate a random key
2. saves a local `secret.txt`

The result is a random and safely hidden `SECRET_KEY`.
"""
try:
    SECRET_KEY
except NameError:
    SECRET_FILE = os.path.join(PROJECT_ROOT, 'secret.key')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
    except IOError:
        try:
            import random
            symbols = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            SECRET_KEY = ''.join([random.SystemRandom().choice(symbols) for i in range(50)])
            with open(SECRET_FILE, 'w') as f:
                f.write(SECRET_KEY)
        except IOError:
            Exception('Please create a %s file with random characters \
            to generate your secret key!' % SECRET_FILE)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'corsheaders',
    'permission',

    'bars_core',
    'bars_items',
    'bars_transactions',
    'bars_news',
    'bars_bugtracker',
)


MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'bars_django.utils.BarMiddleware'
)

ROOT_URLCONF = 'bars_django.urls'

WSGI_APPLICATION = 'bars_django.wsgi.application'

ATOMIC_REQUESTS = True

# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_CHARSET = "utf-8"

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/api/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static/')

# Rest framework

REST_FRAMEWORK = {
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    'DEFAULT_PERMISSION_CLASSES': [
        # 'bars_core.perms.RootBarPermissionsOrAnonReadOnly',
        # 'rest_framework.permissions.AllowAny',
        # 'bars_core.perms.PerBarPermissionsOrAnonReadOnly',
        'rest_framework.permissions.DjangoObjectPermissions',
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # TODO: remove
        'rest_framework.authentication.BasicAuthentication',  # TODO: remove
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter'
    )
}

AUTHENTICATION_BACKENDS = (
    'bars_core.auth.AuthenticationBackend',
    'bars_core.perms.PermissionBackend',
)

import datetime
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=7 * 24),  # Todo: temporary
}

# Permissions

PERMISSION_CHECK_PERMISSION_PRESENCE = False
PERMISSION_DEFAULT_APL_ANY_PERMISSION = False
PERMISSION_DEFAULT_APL_CHANGE_PERMISSION = True
PERMISSION_DEFAULT_APL_DELETE_PERMISSION = False

# CORS headers

CORS_ORIGIN_ALLOW_ALL = True


# API app

AUTH_USER_MODEL = 'bars_core.User'
