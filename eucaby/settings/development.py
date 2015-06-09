
from eucaby.settings.base import *  # pylint: disable=wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'eucaby',
        'USER': 'root',
        'HOST': '/cloudsql/eucaby-dev:eucaby2',
    }
}

DEBUG = False
# ALLOWED_HOSTS = []
