"""
WSGI config for eucaby project.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eucaby.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
