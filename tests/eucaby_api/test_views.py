import unittest
from flask import json
import mock
from eucaby_api import auth
from eucaby_api import models
from eucaby_api import wsgi

class TestOAuthToken(unittest.TestCase):

    def setUp(self):
        self.app = wsgi.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        self.client = self.app.test_client()
        self.grant_password_error = dict(
            code='invalid',
            fields=dict(
                grant_type='Valid grant types are password and refresh_token',
                password='Missing required parameter password',
                service='Invalid service',
                username='Missing required parameter username'
            ),
            message='Invalid request parameters'
        )
        # Facebook responses
        self.fb_invalid_token = dict(
            error=dict(message='Invalid OAuth access token.',
                type='OAuthException', code=190))
        self.fb_valid_token = dict(access_token='someaccesstoken', expires=123)
        self.fb_profile = dict(
            first_name='Test', last_name='User', verified=True,
            name='Test User', locale='en_US', gender='male',
            email='test@example.com', id='12345',
            link='https://www.facebook.com/app_scoped_user_id/12345/',
            timezone=-8, updated_time='2014-12-06T21:31:50+0000')
        # Valid oauth params
        self.valid_params = dict(
            grant_type='password', service='facebook',
            password='test_password', username='12345')
        models.db.app = self.app
        models.db.create_all()

    def tearDown(self):
        models.db.drop_all()

    def testGeneralErrors(self):
        """Tests general errors related to oauth."""
        invalid_grant = dict(
            code='invalid_grant',
            fields=dict(
                grant_type='Valid grant types are password and refresh_token'
            ),
            message='Invalid request parameters'
        )
        # Get is not supported
        resp = self.client.get('/oauth/token')
        self.assertEqual(405, resp._status_code)

        # No parameters
        resp = self.client.post('/oauth/token')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(400, resp._status_code)
        data = json.loads(resp.data)
        self.assertEqual(invalid_grant, data)

        # Invalid grant type
        resp = self.client.post('/oauth/token', dict(grant_type='wrong'))
        self.assertEqual(400, resp._status_code)
        self.assertEqual(invalid_grant, data)

    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def testExchangeInvalidToken(self, fb_exchange_token):
        """Tests invalid Facebook token."""
        # Grant type is set
        resp = self.client.post('/oauth/token', data=dict(grant_type='password'))
        data = json.loads(resp.data)
        assert_data = self.grant_password_error.copy()
        assert_data['fields'].pop('grant_type')
        self.assertEqual(assert_data, data)

        # Invalid token
        fb_exchange_token.side_effect = auth.f_oauth_client.OAuthException(
                self.fb_invalid_token['error']['message'],
                type='token_exchange_failed', data=self.fb_invalid_token)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        invalid_token_resp = dict(
            code='invalid_oauth', message='Invalid OAuth access token.')
        self.assertEqual(invalid_token_resp, data)
        self.assertEqual(403, resp._status_code)

    @mock.patch('eucaby_api.models.utils')
    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def testExchangeValidTokenSuccess(
            self, fb_exchange_token, fb_get, eucaby_utils):
        """Tests successful response."""
        # Valid token, user doesn't exist, fb profile
        fb_exchange_token.return_value = self.fb_valid_token
        fb_get.return_value = self.fb_profile
        UUID = '1a2b3c'
        eucaby_utils.generate_uuid.return_value = UUID
        eucaby_success_resp = dict(
            access_token=UUID, expires_in=models.EXPIRATION_SECONDS,
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=models.TOKEN_TYPE)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp._status_code)

        users = models.User.query.all()
        tokens = models.Token.query.all()
        self.assertEqual(1, len(users))
        self.assertEqual(2, len(tokens))
        user = users[0]
        self.assert_object(
            user, first_name='Test', last_name='User', gender='male',
            email='test@example.com', username='12345')
        fb_token = tokens[0]
        eucaby_token = tokens[1]
        # self.assert

        # Valid token, user exists, fb profile

        # print tokens

        # print resp.data, resp._status_code

    @mock.patch('eucaby_api.models.utils')
    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def testExchangeValidTokenFailed(
            self, fb_exchange_token, fb_get, eucaby_utils):
        """Tests valid token with failed response."""
        self.valid_params['username'] = '54321'
        # Valid token, fb profile, username doesn't match fb profile id
        fb_exchange_token.return_value = self.fb_valid_token
        fb_get.return_value = self.fb_profile
        UUID = '1a2b3c'
        eucaby_utils.generate_uuid.return_value = UUID
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        eucaby_invalid_user = dict(
            code='invalid_user', message='Invalid username')
        self.assertEqual(eucaby_invalid_user, data)
        self.assertEqual(400, resp._status_code)

        # Valid token, user doesn't exist, fb profile error

        # Valid token, user exists, fb profile error


        # token = 'CAALgK0YvBagBAKO3HYZBfVwUDojv6cqnJFblOXFocDgzv4h2mwPsi1i44ZCcXtacOYfB7vAhQRvq7asZCsZCI7tg9xbvAkac7hVcYJvXgkhZA4xl8qzgQk0Dhb1ahIDqw95UtlMlpAk9wb0UGYsLtvkrA3ZBL0A2OZCv7G4ToYKZApq3JumQlZBFp42scHd9ijuLnw1twjYFgJESZARhJuJKxoPcu2hmQkLLEZD'
        # resp = auth.facebook.get('/me', token=(token, ''))
        # print resp.data

        # Expired token
        # ex_token

        # data = json.loads(resp.data)

        # XXX: Finish
        #params['extra'] = 'param'
        # Short-lived token
        # print resp.data


        # # Invalid password
        #
        # # Missing parameters for refresh grant type
        # resp = self.client.post('/oauth/token', dict(grant_type='refresh_token'))
        #


    def testRefreshToken(self):

        # # Invalid refresh token
        #
        # print resp._status_code
        # print resp.data

        # resp = self.client.post(
        #     '/oauth/token', data=dict(
        #         service='facebook', grant_type='password', username='test_user',
        #         password='test_token'))
        # self.assertEqual(200, resp._status_code)
        # # XXX: Add Facebook mock
        pass

    def testAuthRequest(self):
        pass


    def assert_object(self, user, **kwargs):
        for k, v in kwargs.items():
            self.assertEqual(v, getattr(user, k))


if __name__ == '__main__':
    unittest.main()
