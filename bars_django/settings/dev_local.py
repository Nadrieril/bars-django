from .common import *

DEBUG = True

TEMPLATE_DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3'
    }
}


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
