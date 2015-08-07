
from eucaby.settings.base import *  # pylint: disable=wildcard-import,unused-wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'eucaby',
        'USER': 'dev',
        'PASSWORD': 'devpass',
        'HOST': '',
        'PORT': '',
    }
}

EUCABY_URL = 'http://localhost'
