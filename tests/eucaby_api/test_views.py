
import mock
import unittest
from flask import json

from eucaby_api import auth
from eucaby_api import models

from tests.eucaby_api import base as test_base
from tests.utils import utils as test_utils


UUID = '1z2x3c'
UUID2 = '123qweasd'
TOKEN_TYPE = 'Bearer'


class TestOAuthToken(test_base.TestCase):

    def setUp(self):
        super(TestOAuthToken, self).setUp()
        # I couldn't mock oauthlib.oauth2.rfc6749.tokens.random_token_generator
        # so I decided to set the config parameter
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
        self.client = self.app.test_client()
        # Facebook responses
        self.fb_invalid_token = dict(
            error=dict(message='Invalid OAuth access token.',
                       type='OAuthException', code=190))
        self.fb_invalid_method = dict(
            error=dict(message=('(#803) Cannot query users by their '
                                'username (helloworld)'),
                       type='OAuthException', code=803))
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

    def test_general_errors(self):
        """Tests general errors related to oauth."""
        invalid_method_error = dict(
            code='invalid_method', message='Method not allowed')
        invalid_grant_error = dict(
            code='unsupported_grant_type',
            fields=dict(grant_type='Grant type is missing or invalid'),
            message='Grant type is not supported')
        invalid_service_error = dict(
            code='invalid_request',
            fields=dict(service='Missing service parameter'),
            message='Missing service parameter')

        # Get is not supported
        resp = self.client.get('/oauth/token')
        self.assertEqual(405, resp.status_code)
        data = json.loads(resp.data)
        self.assertEqual(invalid_method_error, data)

        # No parameters
        resp = self.client.post('/oauth/token')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(400, resp.status_code)
        data = json.loads(resp.data)
        self.assertEqual(invalid_grant_error, data)

        # Invalid grant type
        resp = self.client.post('/oauth/token', dict(grant_type='wrong'))
        self.assertEqual(400, resp.status_code)
        self.assertEqual(invalid_grant_error, data)

        # Grant type is set
        resp = self.client.post(
            '/oauth/token', data=dict(grant_type='password'))
        data = json.loads(resp.data)
        self.assertEqual(400, resp.status_code)
        self.assertEqual(invalid_service_error, data)

    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_exchange_invalid_token(self, fb_exchange_token):
        """Tests invalid Facebook token."""
        # Invalid token
        fb_exchange_token.side_effect = auth.f_oauth_client.OAuthException(
            self.fb_invalid_token['error']['message'],
            type='token_exchange_failed', data=self.fb_invalid_token)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        invalid_token_resp = dict(
            code='invalid_grant', message='Invalid OAuth access token.')
        self.assertEqual(invalid_token_resp, data)
        self.assertEqual(403, resp.status_code)

    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_exchange_valid_token_success(self, fb_exchange_token, fb_get):
        """Tests successful response for access token."""
        # Test A: Valid token, user doesn't exist, fb profile
        fb_exchange_token.return_value = self.fb_valid_token
        fb_get.return_value = mock.Mock(data=self.fb_profile)
        eucaby_success_resp = dict(
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)
        # Verify user and access tokens
        users = models.User.query.all()
        tokens = models.Token.query.all()
        self.assertEqual(1, len(users))
        self.assertEqual(2, len(tokens))
        user = users[0]
        test_utils.assert_object(
            user, first_name='Test', last_name='User', gender='male',
            email='test@example.com', username='12345')
        fb_token = tokens[0]
        eucaby_token = tokens[1]
        test_utils.assert_object(
            fb_token, service=models.FACEBOOK, user_id=user.id,
            access_token='someaccesstoken', refresh_token=None)
        test_utils.assert_object(
            eucaby_token, service=models.EUCABY, user_id=user.id,
            access_token=UUID, refresh_token=UUID)
        models.Token.query.delete()  # Clean up tokens

        # Test B: Valid token, user exists, fb profile
        fb_params = dict(access_token='anotheraccesstoken')
        self.fb_valid_token.update(fb_params)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)
        # Verify user and access tokens
        users = models.User.query.all()
        tokens = models.Token.query.all()
        self.assertEqual(1, len(users))
        # Every access token request generates tokens
        self.assertEqual(2, len(tokens))
        user = users[0]
        test_utils.assert_object(  # Same user
            user, first_name='Test', last_name='User', gender='male',
            email='test@example.com', username='12345')
        fb_token = tokens[0]
        eucaby_token = tokens[1]
        test_utils.assert_object(
            fb_token, service=models.FACEBOOK, user_id=user.id,
            access_token='anotheraccesstoken', refresh_token=None)
        test_utils.assert_object(
            eucaby_token, service=models.EUCABY, user_id=user.id,
            access_token=UUID, refresh_token=UUID)
        models.Token.query.delete()

        # Test C: Extra parameters are ignored
        self.valid_params['extra'] = 'param'
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)

    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_exchange_valid_token_failed(self, fb_exchange_token, fb_get):
        """Tests valid token with failed response for access token."""
        # Test A: Valid token, user doesn't exist, fb profile error
        fb_exchange_token.return_value = self.fb_valid_token
        side_effect = auth.f_oauth_client.OAuthException(
            self.fb_invalid_method['error']['message'],
            type='token_exchange_failed', data=self.fb_invalid_method)
        fb_get.side_effect = side_effect
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        eucaby_invalid_grant = dict(
            code='invalid_grant',
            message=self.fb_invalid_method['error']['message'])
        self.assertEqual(eucaby_invalid_grant, data)
        self.assertEqual(403, resp.status_code)
        # Verify user and access tokens
        self.assertEqual(0, models.User.query.count())
        self.assertEqual(0, models.Token.query.count())

        # Test B: Valid token, fb profile, username doesn't match fb profile id
        valid_params = self.valid_params.copy()
        valid_params['username'] = '54321'
        fb_get.return_value = mock.Mock(data=self.fb_profile)
        fb_get.side_effect = None
        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        eucaby_invalid_user = dict(
            code='invalid_grant', message='Invalid username')
        self.assertEqual(eucaby_invalid_user, data)
        self.assertEqual(403, resp.status_code)
        self.assertEqual(1, models.User.query.count())
        self.assertEqual(0, models.Token.query.count())
        models.Token.query.delete()

        # Test C:
        # Valid token, user exists, fb profile error
        # FB profile error doesn't affect access tokens creation
        eucaby_success_resp = dict(
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)
        fb_get.side_effect = side_effect
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)
        # Verify user and access tokens
        self.assertEqual(1, models.User.query.count())
        self.assertEqual(2, models.Token.query.count())

    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_refresh_token(self, fb_exchange_token, fb_get):
        """Tests refresh token."""
        # Grant type is set
        resp = self.client.post('/oauth/token',
                                data=dict(grant_type='refresh_token'))
        data = json.loads(resp.data)
        invalid_refresh_token_error = dict(
            code='invalid_request',
            fields=dict(refresh_token='Missing refresh_token parameter'),
            message='Missing refresh token parameter.')
        self.assertEqual(invalid_refresh_token_error, data)
        self.assertEqual(400, resp.status_code)
        # Create token
        fb_exchange_token.return_value = self.fb_valid_token
        fb_get.return_value = mock.Mock(data=self.fb_profile)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        refresh_token = data['refresh_token']

        # Valid refresh token
        # Note: I tried to change token generator to return UUID2 but
        #   server method is being cached and I couldn't change it
        valid_params = dict(
            grant_type='refresh_token', refresh_token=refresh_token)
        eucaby_success_resp = dict(
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)

        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)

        # Invalid refresh token
        valid_params = dict(grant_type='refresh_token', refresh_token='hello')
        eucaby_error_resp = dict(
            message='Invalid refresh token', code='invalid_grant')
        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_error_resp, data)
        self.assertEqual(403, resp.status_code)


if __name__ == '__main__':
    unittest.main()
