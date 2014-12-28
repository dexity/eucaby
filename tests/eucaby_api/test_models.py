
import mock
import unittest
from eucaby_api import models
from eucaby_api import wsgi
from tests.utils import utils as test_utils

class TestViews(unittest.TestCase):

    def setUp(self):
        self.app = wsgi.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        models.db.app = self.app
        models.db.create_all()
        self.user = models.User(
            username='2345', first_name='Test', last_name='User',
            email='test@example.com')
        models.db.session.add(self.user)
        models.db.session.commit()

    def tearDown(self):
        models.db.drop_all()

    def test_create_facebook_token(self):
        """Tests create facebook token."""
        params = dict(user_id=self.user.id, access_token='123qweasd',
                      expires_seconds=5)
        token = models.Token.create_facebook_token(**params)

        test_utils.assert_object(
            token, user_id=self.user.id, service=models.FACEBOOK,
            access_token=params['access_token'], refresh_token=None)
        self.assertEqual(1, models.Token.query.count())

    @mock.patch('eucaby_api.models.utils')
    def test_create_or_update_eucaby_token(self, eucaby_utils):
        """Tests create and update eucaby token."""
        UUID = '1a2b3c'
        eucaby_utils.generate_uuid.return_value = UUID
        token = models.Token.create_eucaby_token(self.user.id)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=UUID, refresh_token=UUID)
        self.assertEqual(1, models.Token.query.count())

        # Refresh token exists
        UUID2 = '123qweasd'
        eucaby_utils.generate_uuid.return_value = UUID2
        token = models.Token.update_token(UUID)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=UUID2, refresh_token=UUID)
        # Refresh token doesn't exist
        token = models.Token.update_token('wrongtoken')
        self.assertIsNone(token)


if __name__ == "__main__":
    unittest.main()
