"""
WSGI config for bars_django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "bars_django.settings.dev_local"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


# From http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
# import django.core.management
# utility = django.core.management.ManagementUtility()
# command = utility.fetch_command('runserver_plus')

# command.validate()

# import django.core.handlers.wsgi

# application = django.core.handlers.wsgi.WSGIHandler()
