import os
import sys
import django.core.handlers.wsgi as django_wsgi

sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
os.environ["DJANGO_SETTINGS_MODULE"] = "eucaby.eucaby.settings"

application = django_wsgi.WSGIHandler()