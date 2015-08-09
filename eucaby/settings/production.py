
from eucaby.settings.base import *  # pylint: disable=wildcard-import

DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'eucaby',
        'USER': 'root',
        'HOST': '/cloudsql/eucaby-prd:eucaby',
        'OPTIONS': {
            'init_command': 'SET storage_engine=INNODB',
        }
    }
}

EUCABY_URL = 'http://eucaby-prd.appspot.com'
# ALLOWED_HOSTS = []
