
import unittest
from eucaby_api import models
from eucaby_api import wsgi


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = wsgi.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        models.db.app = self.app
        models.db.drop_all()  # Drop in case some tables are left
        models.db.create_all()

    def tearDown(self):
        models.db.session.close()
        models.db.drop_all()
