"""
WSGI config for eucaby project.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
