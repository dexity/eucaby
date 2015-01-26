
import unittest
from eucaby_api import models
from tests.eucaby_api import base as test_base
from tests.eucaby_api import fixtures
from tests.utils import utils as test_utils


class TestModels(test_base.TestCase):

    def setUp(self):
        super(TestModels, self).setUp()
        self.user = models.User(
            username='2345', first_name='Test', last_name='User',
            email='test@example.com')
        models.db.session.add(self.user)
        models.db.session.commit()

    def test_create_facebook_token(self):
        """Tests create facebook token."""
        params = dict(user_id=self.user.id, access_token='123qweasd',
                      expires_seconds=5)
        token = models.Token.create_facebook_token(**params)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.FACEBOOK,
            access_token=params['access_token'], refresh_token=None)
        self.assertEqual(1, models.Token.query.count())

    def test_create_or_update_eucaby_token(self):
        """Tests create and update eucaby token."""
        token_dict = dict(
            access_token=fixtures.UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=fixtures.UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
        token = models.Token.create_eucaby_token(self.user.id, token_dict)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=fixtures.UUID, refresh_token=fixtures.UUID)
        self.assertEqual(1, models.Token.query.count())

        token_dict['access_token'] = fixtures.UUID2
        # Refresh token exists
        token.update_token(token_dict)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=fixtures.UUID2, refresh_token=fixtures.UUID)


if __name__ == '__main__':
    unittest.main()
