import unittest

from eucaby_api import app as eucaby_app
from eucaby_api.utils import utils as api_utils


class UtilsTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')

    def test_payload_data(self):
        """Tests payload data."""
        # Empty parameters
        data = api_utils.gcm_payload_data(None, '')
        self.assertEqual(
            dict(title='Eucaby', message='New incoming messages'), data)
        # Name parameter is set
        data = api_utils.gcm_payload_data('Full Name', '')
        self.assertEqual(
            dict(title='Full Name', message='New incoming messages'), data)
        # Message type is set
        data = api_utils.gcm_payload_data(None, 'something')
        self.assertEqual(
            dict(title='Eucaby', message='sent you a new something'), data)
        # Name and message are set
        data = api_utils.gcm_payload_data('Full Name', 'something')
        self.assertEqual(
            dict(title='Full Name', message='sent you a new something'), data)


if __name__ == '__main__':
    unittest.main()
