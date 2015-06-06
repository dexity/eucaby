# -*- coding: utf-8 -*-

import unittest

from eucaby_api import app as eucaby_app
from eucaby_api.utils import utils as api_utils


class UtilsTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')

    def test_gcm_payload_data(self):
        """Tests GCM payload data."""
        # Empty parameters
        data = api_utils.gcm_payload_data(None, '')
        self.assertEqual(
            dict(title='Eucaby', message='New incoming messages'), data)
        # Name parameter is set
        data = api_utils.gcm_payload_data(u'Юзер', '')
        self.assertEqual(
            dict(title=u'Юзер', message='New incoming messages'), data)
        # Message type is set
        data = api_utils.gcm_payload_data(None, 'something')
        self.assertEqual(
            dict(title='Eucaby', message='sent you a new something'), data)
        # Name and message are set
        data = api_utils.gcm_payload_data(u'Юзер', 'something')
        self.assertEqual(
            dict(title=u'Юзер', message='sent you a new something'), data)

    def test_apns_payload_data(self):
        """Tests APNs payload data."""
        # Empty parameters
        data = api_utils.apns_payload_data(None, '')
        self.assertEqual(dict(alert='Eucaby\nNew incoming messages',
                              sound='default'), data)
        # Name parameter is set
        data = api_utils.apns_payload_data(u'Юзер', '')
        self.assertEqual(dict(alert=u'Юзер\nNew incoming messages',
                              sound='default'), data)
        # Message type is set
        data = api_utils.apns_payload_data(None, 'something')
        self.assertEqual(dict(alert='Eucaby\nsent you a new something',
                              sound='default'), data)
        # Name and message are set
        data = api_utils.apns_payload_data(u'Юзер', 'something')
        self.assertEqual(dict(alert=u'Юзер\nsent you a new something',
                              sound='default'), data)


if __name__ == '__main__':
    unittest.main()
