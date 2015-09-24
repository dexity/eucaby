import unittest

from eucaby_api import config
from eucaby_api import models
from eucaby_api import app as eucaby_app


class Testing(config.Config):

    """Testing configuration."""
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqldb://test:testpass@localhost/test_eucaby?'
        'charset=utf8&use_unicode=0')
    FACEBOOK = dict(
        consumer_key='12345',
        consumer_secret='secret'
    )
    TESTING = True
    DEBUG = True


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object(Testing)
        models.db.app = self.app
        models.db.drop_all()  # Drop in case some tables are left
        models.db.create_all()

    def tearDown(self):
        models.db.session.close()
        models.db.drop_all()
