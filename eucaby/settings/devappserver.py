
from eucaby.settings.base import *  # pylint: disable=wildcard-import,unused-wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'eucaby',
        'USER': 'dev',
        'PASSWORD': 'devpass',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'init_command': 'SET storage_engine=INNODB',
        }
    }
}

EUCABY_URL = 'http://localhost'
ENV_TYPE = 'devappserver'
