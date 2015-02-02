"""API configuration."""

from eucaby_api import secret_keys


class Config(object):

    """General configuration."""
    SECRET_KEY = secret_keys.CSRF_SECRET_KEY
    CSRF_SESSION_KEY = secret_keys.SESSION_KEY
    OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 60 * 60 * 24 * 30  # 30 days  pylint: disable=invalid-name
    FACEBOOK = dict(
        consumer_key='809426419123624',
        consumer_secret='b4b8c000e74e15c294e9d67ce7fca42b'
    )
    CSRF_ENABLED = True
    CACHE_TYPE = 'gaememcached'
    # XXX: Make host url configurable
    EUCABY_URL = 'http://localhost:8888'
    NOREPLY_EMAIL = 'alex@eucaby.com'


class Testing(Config):

    """Testing configuration."""
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://test:testpass@localhost/test_eucaby'
        '?charset=utf8&use_unicode=0')
    FACEBOOK = dict(
        consumer_key='12345',
        consumer_secret='secret'
    )
    TESTING = True
    DEBUG = True


class LocalDevelopment(Config):

    """Development configuration."""
    DEBUG = True
    APP_ID = 'eucaby-dev'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://dev:devpass@localhost/eucaby'
        '?charset=utf8&use_unicode=0')
    # Flask-DebugToolbar settings
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class RemoteProduction(Config):

    """Remote production configuration."""
    # Use Cloud SQL from local command line
    APP_ID = 'eucaby-prd'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://root:eucaby2pass@173.194.232.127/eucaby'
        '?charset=utf8&use_unicode=0')


class RemoteDevelopment(Config):

    """Remote development configuration."""
    # Use Cloud SQL from local command line
    APP_ID = 'eucaby-dev'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://root:devpass@173.194.84.204/eucaby'
        '?charset=utf8&use_unicode=0')


class Development(Config):

    """Development configuration."""
    DEBUG = False
    APP_ID = 'eucaby-dev'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+gaerdbms:///eucaby?instance=eucaby-dev:eucaby2')
    EUCABY_URL = 'http://eucaby-dev.appspot.com'


class Production(Config):

    """Production configuration."""
    DEBUG = False
    APP_ID = 'eucaby-prd'
    SQLALCHEMY_DATABASE_URI = (
        'mysql+gaerdbms:///eucaby?instance=eucaby-prd:eucaby')
    EUCABY_URL = 'http://eucaby-prd.appspot.com'
