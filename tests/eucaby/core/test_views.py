
import os
from eucaby.settings import utils as set_utils
os.environ['DJANGO_SETTINGS_MODULE'] = set_utils.get_settings_module('testing')

from django import test


class TestNotifyLocationView(test.TestCase):

    def setUp(self):
        self.client = test.Client()

    def tearDown(self):
        pass

    def test_get(self):
        resp = self.client.get('/request/123')
        print resp
