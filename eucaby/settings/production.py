
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

EUCABY_URL = 'https://www.eucaby.com'
ENV_TYPE = 'production'
# ALLOWED_HOSTS = []
