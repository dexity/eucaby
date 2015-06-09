
from eucaby.settings.base import *  # pylint: disable=wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test_eucaby',
        'USER': 'test',
        'PASSWORD': 'testpass',
        'HOST': '',
        'PORT': '',
    }
}
