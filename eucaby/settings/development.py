
from eucaby.settings.base import *  # pylint: disable=wildcard-import

DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'eucaby',
        'USER': 'root',
        'HOST': '/cloudsql/eucaby-dev:eucaby2',
    }
}

EUCABY_URL = 'http://eucaby-dev.appspot.com'
# ALLOWED_HOSTS = []
