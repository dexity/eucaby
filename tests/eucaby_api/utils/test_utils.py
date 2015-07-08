# -*- coding: utf-8 -*-

import unittest

from eucaby_api import args as api_args
from eucaby_api import app as eucaby_app
from eucaby_api.utils import utils as api_utils


class UtilsTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        self.cases = (
            (None, '', ''),  # Empty parameters
            (u'Юзер', '', ''),  # Name parameter is set
            (None, 'something', '123'),  # Message type and id are set
            (u'Юзер', api_args.NOTIFICATION, 123))  # All parameters are set

    def test_payload_data(self):
        """Tests payload data."""
        excepted = (
            dict(title='Eucaby', message='New incoming messages'),
            dict(title=u'Юзер', message='New incoming messages'),
            dict(title='Eucaby', message='sent you a new something'),
            dict(title=u'Юзер', message='sent you a new location'))
        for i, case in enumerate(self.cases):
            data = api_utils.payload_data(*case[:2])
            self.assertEqual(excepted[i], data)

    def test_gcm_payload_data(self):
        """Tests GCM payload data."""
        excepted = (
            dict(title='Eucaby', message='New incoming messages',
                 type='', id=''),
            dict(title=u'Юзер', message='New incoming messages',
                 type='', id=''),
            dict(title='Eucaby', message='sent you a new something',
                 type='something', id='123'),
            dict(title=u'Юзер', message='sent you a new location',
                 type='notification', id=123))
        for i, case in enumerate(self.cases):
            data = api_utils.gcm_payload_data(*case)
            self.assertEqual(excepted[i], data)

    def test_apns_payload_data(self):
        """Tests APNs payload data."""
        excepted = (
            dict(alert='Eucaby\nNew incoming messages', sound='default',
                 custom=dict(type='', id='')),
            dict(alert=u'Юзер\nNew incoming messages', sound='default',
                 custom=dict(type='', id='')),
            dict(alert='Eucaby\nsent you a new something', sound='default',
                 custom=dict(type='something', id='123')),
            dict(alert=u'Юзер\nsent you a new location', sound='default',
                 custom=dict(type='notification', id=123)))
        for i, case in enumerate(self.cases):
            data = api_utils.apns_payload_data(*case)
            self.assertEqual(excepted[i], data)


if __name__ == '__main__':
    unittest.main()
