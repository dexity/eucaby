import unittest

from eucaby_api import app as eucaby_app
from tests.utils import utils as test_utils


class GaeUtilsTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        self.client = self.app.test_client()

    def test_send_notifications(self):
        """Tests send notifications."""
        # test_utils.verify_push_notifications(taskq, client, data)

if __name__ == '__main__':
    unittest.main()