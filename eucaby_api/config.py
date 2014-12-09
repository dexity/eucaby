

class Config(object):
    # SECRET_KEY = CSRF_SECRET_KEY
    # CSRF_SESSION_KEY = SESSION_KEY
    DATABASE_NAME = ''
    DATABASE_USERNAME = ''
    DATABASE_PASSWORD = ''
    FACEBOOK = dict(
        consumer_key='809426419123624',
        consumer_secret='b4b8c000e74e15c294e9d67ce7fca42b'
    )
    CSRF_ENABLED = True
    CACHE_TYPE = 'gaememcached'

class Development(Config):
    DEBUG = True
    # Flask-DebugToolbar settings
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

class Testing(Config):
    FACEBOOK = dict(
        consumer_key='12345',
        consumer_secret='secret'
    )
    TESTING = True
    DEBUG = True

class Production(Config):
    DEBUG = False