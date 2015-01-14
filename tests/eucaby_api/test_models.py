
import unittest
from eucaby_api import models
from tests.eucaby_api import base as test_base
from tests.utils import utils as test_utils


UUID = '1a2b3c'
UUID2 = '123qweasd'
TOKEN_TYPE = 'Bearer'


class TestModels(test_base.TestCase):

    def setUp(self):
        super(TestModels, self).setUp()
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
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
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)
        token = models.Token.create_eucaby_token(self.user.id, token_dict)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=UUID, refresh_token=UUID)
        self.assertEqual(1, models.Token.query.count())

        token_dict['access_token'] = UUID2
        # Refresh token exists
        token = models.Token.update_token(token, token_dict)
        test_utils.assert_object(
            token, user_id=self.user.id, service=models.EUCABY,
            access_token=UUID2, refresh_token=UUID)
        token_dict['refresh_token'] = 'wrongtoken'
        # Refresh token doesn't exist, None is passed for token
        self.assertRaises(
            AttributeError, models.Token.update_token, None, token_dict)


if __name__ == '__main__':
    unittest.main()
