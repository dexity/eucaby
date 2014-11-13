
import os
import django.core.handlers.wsgi as django_wsgi

os.environ["DJANGO_SETTINGS_MODULE"] = "eucaby.eucaby.settings"

application = django_wsgi.WSGIHandler()