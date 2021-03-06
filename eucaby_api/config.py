"""API configuration."""

import os
from eucaby_api import secret_keys

PRD_APP_ID = 'eucaby-prd'
DEV_APP_ID = 'eucaby-dev'
LOCAL_APP_ID = 'local-dev'


class Config(object):

    """General configuration."""
    APP_ID = LOCAL_APP_ID
    SECRET_KEY = secret_keys.CSRF_SECRET_KEY
    CSRF_SESSION_KEY = secret_keys.SESSION_KEY
    OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 60 * 60 * 24 * 30  # 30 days  pylint: disable=invalid-name
    FACEBOOK = dict(  # v2.1
        consumer_key='809426419123624',
        consumer_secret='b4b8c000e74e15c294e9d67ce7fca42b'
    )
    CSRF_ENABLED = True
    CORS_ENABLED = True
    CACHE_TYPE = 'gaememcached'
    EUCABY_URL = 'https://www.eucaby.com'
    NOREPLY_EMAIL = 'notification@eucaby.com'
    GCM_API_KEY = 'AIzaSyApFKUOZoJffYaeD_TjvPKjORWp1JiBdMc'
    APNS_CERT_FILE = os.path.abspath('private/dev/EucabyCert.pem')
    APNS_KEY_FILE = os.path.abspath('private/dev/EucabyKey.pem')
    APNS_USE_SANDBOX = True


class LocalDevelopment(Config):

    """Development configuration."""
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://dev:devpass@localhost/eucaby?'
        'charset=utf8&use_unicode=0')
    DEBUG = True


class RemoteProduction(Config):

    """Remote production configuration."""
    # Use Cloud SQL from local command line
    APP_ID = PRD_APP_ID
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://root:eucaby2pass@173.194.232.127/eucaby?'
        'charset=utf8&use_unicode=0')


class RemoteDevelopment(Config):

    """Remote development configuration."""
    # Use Cloud SQL from local command line
    APP_ID = DEV_APP_ID
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://root:devpass@173.194.84.204/eucaby?'
        'charset=utf8&use_unicode=0')


class Development(Config):

    """Development configuration."""
    APP_ID = DEV_APP_ID
    SQLALCHEMY_DATABASE_URI = (
        'mysql://root@/eucaby?unix_socket=/cloudsql/eucaby-dev:eucaby2')
    EUCABY_URL = 'http://eucaby-dev.appspot.com'
    DEBUG = False


class Production(Config):

    """Production configuration."""
    APP_ID = PRD_APP_ID
    SQLALCHEMY_DATABASE_URI = (
        'mysql://root@/eucaby?unix_socket=/cloudsql/eucaby-prd:eucaby')
    FACEBOOK = dict(  # v2.4
        consumer_key='1622022934714935',
        consumer_secret='e464952b788b20f9101c7454c7816fe4'
    )
    EUCABY_URL = 'https://www.eucaby.com'
    DEBUG = False
    CORS_ENABLED = False
    GCM_API_KEY = 'AIzaSyBouvxkvhXJyZMnR1R_55AIn5WylvZKdlA'
    APNS_CERT_FILE = os.path.abspath('private/prd/EucabyCert.pem')
    APNS_KEY_FILE = os.path.abspath('private/prd/EucabyKey.pem')
    APNS_USE_SANDBOX = False


CONFIG_MAP = {
    DEV_APP_ID: 'eucaby_api.config.Development',
    PRD_APP_ID: 'eucaby_api.config.Production',
    'default': 'eucaby_api.config.LocalDevelopment'
}
