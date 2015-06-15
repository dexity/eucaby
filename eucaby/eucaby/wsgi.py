"""WSGI config for eucaby application."""

import os
from eucaby.settings import utils
from google.appengine.api import app_identity


gae_project_id = app_identity.get_application_id()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', utils.get_settings_module(gae_project_id))

from django.core import wsgi
app = wsgi.get_wsgi_application()
