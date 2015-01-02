
import mock
import unittest
from flask import json

from eucaby_api import auth
from eucaby_api import models

from tests.eucaby_api import base as test_base
from tests.utils import utils as test_utils


UUID = '1z2x3c'
UUID2 = '123qweasd'


class TestOAuthToken(test_base.TestCase):

    def setUp(self):
        super(TestOAuthToken, self).setUp()
        self.client = self.app.test_client()
        self.grant_password_error = dict(
            code='invalid',
            fields=dict(
                grant_type='Valid grant types are password and refresh_token',
                password='Missing required parameter password',
                service='Invalid service',
                username='Missing required parameter username'),
            message='Invalid request parameters')
        self.grant_refresh_error = dict(
            code='invalid',
            fields=dict(
                refresh_token='Missing required parameter refresh_token'),
            message='Invalid request parameters')
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
        invalid_grant_error = dict(
            code='invalid_grant',
            fields=dict(
                grant_type='Valid grant types are password and refresh_token'
            ),
            message='Invalid request parameters'
        )
        extra_params_error = dict(
            fields=dict(extra='Unrecognized parameter'),
            message='Invalid request parameters', code='invalid')
        # Get is not supported
        resp = self.client.get('/oauth/token')
        self.assertEqual(405, resp.status_code)

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

        # Extra parameters
        self.valid_params['extra'] = 'param'
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(extra_params_error, data)

    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_exchange_invalid_token(self, fb_exchange_token):
        """Tests invalid Facebook token."""
        # Grant type is set
        resp = self.client.post(
            '/oauth/token', data=dict(grant_type='password'))
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
        self.assertEqual(403, resp.status_code)

    @mock.patch('eucaby_api.models.utils')
    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_exchange_valid_token_success(
            self, fb_exchange_token, fb_get, eucaby_utils):
        """Tests successful response for access token."""
        # Test A: Valid token, user doesn't exist, fb profile
        fb_exchange_token.return_value = self.fb_valid_token
        fb_get.return_value = mock.Mock(data=self.fb_profile)
        eucaby_utils.generate_uuid.return_value = UUID
        eucaby_success_resp = dict(
            access_token=UUID, expires_in=models.EXPIRATION_SECONDS,
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=models.TOKEN_TYPE)
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

        # Test B: Valid token, user exists, fb profile
        eucaby_utils.generate_uuid.return_value = UUID2
        params = dict(access_token=UUID2, refresh_token=UUID2)
        fb_params = dict(access_token='anotheraccesstoken')
        self.fb_valid_token.update(fb_params)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        eucaby_success_resp.update(params)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)
        # Verify user and access tokens
        users = models.User.query.all()
        tokens = models.Token.query.all()
        self.assertEqual(1, len(users))
        # Every access token request generates tokens
        self.assertEqual(4, len(tokens))
        test_utils.assert_object(  # Same user
            user, first_name='Test', last_name='User', gender='male',
            email='test@example.com', username='12345')
        fb_token = tokens[2]
        eucaby_token = tokens[3]
        test_utils.assert_object(
            fb_token, service=models.FACEBOOK, user_id=user.id,
            access_token='anotheraccesstoken', refresh_token=None)
        test_utils.assert_object(
            eucaby_token, service=models.EUCABY, user_id=user.id,
            access_token=UUID2, refresh_token=UUID2)

    @mock.patch('eucaby_api.models.utils')
    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_exchange_valid_token_failed(
            self, fb_exchange_token, fb_get, eucaby_utils):
        """Tests valid token with failed response for access token."""
        # Test A: Valid token, user doesn't exist, fb profile error
        fb_exchange_token.return_value = self.fb_valid_token
        side_effect = auth.f_oauth_client.OAuthException(
            self.fb_invalid_method['error']['message'],
            type='token_exchange_failed', data=self.fb_invalid_method)
        fb_get.side_effect = side_effect
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        eucaby_invalid_oauth = dict(
            code='invalid_oauth',
            message=self.fb_invalid_method['error']['message'])
        self.assertEqual(eucaby_invalid_oauth, data)
        self.assertEqual(401, resp.status_code)
        # Verify user and access tokens
        self.assertEqual(0, models.User.query.count())
        self.assertEqual(0, models.Token.query.count())

        # Test B: Valid token, fb profile, username doesn't match fb profile id
        valid_params = self.valid_params.copy()
        valid_params['username'] = '54321'
        fb_get.return_value = mock.Mock(data=self.fb_profile)
        fb_get.side_effect = None
        eucaby_utils.generate_uuid.return_value = UUID
        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        eucaby_invalid_user = dict(
            code='invalid_user', message='Invalid username')
        self.assertEqual(eucaby_invalid_user, data)
        self.assertEqual(400, resp.status_code)
        self.assertEqual(1, models.User.query.count())
        self.assertEqual(0, models.Token.query.count())

        # Test C:
        # Valid token, user exists, fb profile error
        # FB profile error doesn't affect access tokens creation
        eucaby_success_resp = dict(
            access_token=UUID, expires_in=models.EXPIRATION_SECONDS,
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=models.TOKEN_TYPE)
        fb_get.side_effect = side_effect
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)
        # Verify user and access tokens
        self.assertEqual(1, models.User.query.count())
        self.assertEqual(2, models.Token.query.count())

    @mock.patch('eucaby_api.models.utils')
    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def test_refresh_token(self, fb_exchange_token, fb_get, eucaby_utils):
        """Tests refresh token."""
        # Grant type is set
        resp = self.client.post('/oauth/token',
                                data=dict(grant_type='refresh_token'))
        data = json.loads(resp.data)
        self.assertEqual(self.grant_refresh_error, data)
        self.assertEqual(400, resp.status_code)
        # Create token
        fb_exchange_token.return_value = self.fb_valid_token
        fb_get.return_value = mock.Mock(data=self.fb_profile)
        eucaby_utils.generate_uuid.return_value = UUID
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        refresh_token = data['refresh_token']

        # Valid refresh token
        valid_params = dict(
            grant_type='refresh_token', refresh_token=refresh_token)
        eucaby_utils.generate_uuid.return_value = UUID2
        eucaby_success_resp = dict(
            access_token=UUID2, expires_in=models.EXPIRATION_SECONDS,
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=models.TOKEN_TYPE)
        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_success_resp, data)
        self.assertEqual(200, resp.status_code)

        # Invalid refresh token
        valid_params = dict(grant_type='refresh_token', refresh_token='hello')
        eucaby_error_resp = dict(
            message='Invalid refresh token', code='invalid_token')
        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        self.assertEqual(eucaby_error_resp, data)
        self.assertEqual(404, resp.status_code)


if __name__ == '__main__':
    unittest.main()
