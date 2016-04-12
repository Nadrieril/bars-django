from .common import *

ALLOWED_HOSTS = [ "*" ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',
        'HOST': 'mysqldb',
        'USER': 'root',
        'PASSWORD': 'root',
    }
}

ADMINS = (("Babe", "babe@binets.polytechnique.fr"),)
SERVER_EMAIL = 'babe@binets.polytechnique.fr'

SLACK_HOOK = True
# Kuzh - for Slack hook requests
PROXIES = {
    "http": "http://129.104.247.2:8080/",
    "https": "http://129.104.247.2:8080/"
}

# Logging - Slack notifications on Error 500
SLACK_WEBHOOK_ERROR_URL = "https://hooks.slack.com/services/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"
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'slack': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'bars_django.slack_handler.SlackHandler'
        }
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'filters': ['require_debug_false'],
        #     'class': 'django.utils.log.AdminEmailHandler'
        # }
    },
    'loggers': {
        'django.request': {
            'handlers': ['slack'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
