
import datetime
import mock
import unittest
from flask import json

from eucaby_api import auth
from eucaby_api import models

from tests.eucaby_api import base as test_base
from tests.eucaby_api import fixtures
from tests.utils import utils as test_utils


UUID = '1z2x3c'
UUID2 = '123qweasd'
TOKEN_TYPE = 'Bearer'


class GeneralTest(test_base.TestCase):

    def setUp(self):
        super(GeneralTest, self).setUp()
        self.client = self.app.test_client()

    def test_invalid_endpoint(self):
        resp = self.client.get('/wrong')
        not_found_error = dict(code='invalid_request', message='Not found')
        data = json.loads(resp.data)
        self.assertEqual(not_found_error, data)
        self.assertEqual(404, resp.status_code)


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
        ec_success_resp = dict(
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(ec_success_resp, data)
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
        ec_token = tokens[1]
        test_utils.assert_object(
            fb_token, service=models.FACEBOOK, user_id=user.id,
            access_token='someaccesstoken', refresh_token=None)
        test_utils.assert_object(
            ec_token, service=models.EUCABY, user_id=user.id,
            access_token=UUID, refresh_token=UUID)
        models.Token.query.delete()  # Clean up tokens

        # Test B: Valid token, user exists, fb profile
        fb_params = dict(access_token='anotheraccesstoken')
        self.fb_valid_token.update(fb_params)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(ec_success_resp, data)
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
        ec_token = tokens[1]
        test_utils.assert_object(
            fb_token, service=models.FACEBOOK, user_id=user.id,
            access_token='anotheraccesstoken', refresh_token=None)
        test_utils.assert_object(
            ec_token, service=models.EUCABY, user_id=user.id,
            access_token=UUID, refresh_token=UUID)
        models.Token.query.delete()

        # Test C: Extra parameters are ignored
        self.valid_params['extra'] = 'param'
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(ec_success_resp, data)

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
        ec_invalid_grant = dict(
            code='invalid_grant',
            message=self.fb_invalid_method['error']['message'])
        self.assertEqual(ec_invalid_grant, data)
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
        ec_invalid_user = dict(
            code='invalid_grant', message='Invalid username')
        self.assertEqual(ec_invalid_user, data)
        self.assertEqual(403, resp.status_code)
        self.assertEqual(1, models.User.query.count())
        self.assertEqual(0, models.Token.query.count())
        models.Token.query.delete()

        # Test C:
        # Valid token, user exists, fb profile error
        # FB profile error doesn't affect access tokens creation
        ec_success_resp = dict(
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)
        fb_get.side_effect = side_effect
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        self.assertEqual(ec_success_resp, data)
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
        ec_success_resp = dict(
            access_token=UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=TOKEN_TYPE)

        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        self.assertEqual(ec_success_resp, data)
        self.assertEqual(200, resp.status_code)

        # Invalid refresh token
        valid_params = dict(grant_type='refresh_token', refresh_token='hello')
        ec_error_resp = dict(
            message='Invalid refresh token', code='invalid_grant')
        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        self.assertEqual(ec_error_resp, data)
        self.assertEqual(403, resp.status_code)


class TestFriends(test_base.TestCase):

    def setUp(self):
        super(TestFriends, self).setUp()
        self.client = self.app.test_client()
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
        fixtures.create_user_account(self.client)

    @mock.patch('eucaby_api.auth.facebook._tokengetter')
    def test_general_errors(self, fb_tokengetter):
        """Tests general errors."""
        # Note: Some of the tests are general to all oauth requests
        # Test A: No token is passed
        ec_unauthorized_error = dict(
            code='invalid_token', message='Invalid access token')
        resp = self.client.get('/friends')
        data = json.loads(resp.data)
        self.assertEqual(ec_unauthorized_error, data)
        self.assertEqual(401, resp.status_code)

        # Test B: Invalid Eucaby token
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format('wrong')))
        data = json.loads(resp.data)
        self.assertEqual(ec_unauthorized_error, data)
        self.assertEqual(401, resp.status_code)

        # Test C: No Facebook token, valid Eucaby token
        fb_no_token_error = dict(
            code='service_error', message='No token available')
        fb_tokengetter.return_value = None
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(fb_no_token_error, data)
        self.assertEqual(400, resp.status_code)

        # Test D: Invalid Facebook token, valid Eucaby token
        fb_invalid_token_error = dict(
            error=dict(code=190, message='Invalid OAuth access token.',
                       type='OAuthException'))
        ec_service_error = dict(
            code='service_error', message='Invalid OAuth access token.')
        with mock.patch('eucaby_api.auth.facebook.request') as fb_request:
            fb_request.return_value = mock.Mock(
                data=fb_invalid_token_error, status=401)
            fb_tokengetter.return_value = ('wrong', '')
            resp = self.client.get(
                '/friends', headers=dict(
                    Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_service_error, data)
        self.assertEqual(401, resp.status_code)

        # Test E: Eucaby token expired
        ec_token = models.Token.query.filter_by(service=models.EUCABY)[0]
        ec_token.expires = ec_token.expires - datetime.timedelta(days=31)
        self.app.db.session.add(ec_token)
        self.app.db.session.commit()
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_unauthorized_error, data)
        self.assertEqual(401, resp.status_code)

        # Test F: User is not active
        ec_token.expires = datetime.datetime.now() + datetime.timedelta(days=30)
        ec_token.user.is_active = False
        self.app.db.session.add(ec_token)
        self.app.db.session.commit()
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_unauthorized_error, data)
        self.assertEqual(401, resp.status_code)

    @mock.patch('eucaby_api.auth.facebook.request')
    def test_friends(self, fb_request):
        """Tests successful response for access token."""
        # List of friends
        fb_friends = dict(
            data=[dict(name='User1', id='123'), dict(name='User2', id='456')],
            paging=dict(
                next=('https://graph.facebook.com/v2.1/10152815532718638/'
                      'friends?limit=5000&offset=5000&__after_id=enc_Aez53')),
            summary=dict(total_count=123))
        ec_resp = dict(
            data=[dict(name='User1', username='123'),
                  dict(name='User2', username='456')])
        fb_request.return_value = mock.Mock(data=fb_friends, status=200)
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_resp, data)
        self.assertEqual(200, resp.status_code)

        # Empty list of friends
        fb_friends['data'] = []
        fb_request.return_value = mock.Mock(data=fb_friends, status=200)
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(dict(data=[]), data)
        self.assertEqual(200, resp.status_code)


class TestRequestLocation(test_base.TestCase):

    def setUp(self):
        super(TestRequestLocation, self).setUp()
        self.client = self.app.test_client()
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
        fixtures.create_user_account(self.client)

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        ec_invalid_method = dict(
            message='Method not allowed', code='invalid_method')
        resp = self.client.get('/location/request')
        data = json.loads(resp.data)
        self.assertEqual(ec_invalid_method, data)
        self.assertEqual(405, resp.status_code)

        # No parameters
        ec_missing_params = dict(
            message='Missing email or username parameters',
            code='invalid_request')
        resp = self.client.post(
            '/location/request',
            headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_missing_params, data)
        self.assertEqual(400, resp.status_code)

        # Invalid recipient email address
        ec_invalid_email = dict(
            fields=dict(email='Missing email or username parameters'),
            message='Invalid request parameters', code='invalid_request')
        resp = self.client.post(
            '/location/request', data=dict(email='wrong'),
            headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_invalid_email, data)
        self.assertEqual(400, resp.status_code)

        # Invalid recipient (not found or inactive)
        resp = self.client.post(
            '/location/request', data=dict(username='456'),
            headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        ec_user_not_found = dict(message='User not found', code='not_found')
        self.assertEqual(ec_user_not_found, data)
        self.assertEqual(404, resp.status_code)

    def test_success(self):
        # Valid email address
        resp = self.client.post(
            '/location/request', data=dict(email='test@example.com'),
            headers=dict(Authorization='Bearer {}'.format(UUID)))
        data = json.loads(resp.data)
        # ec_user_not_found = dict(message='User not found', code='not_found')
        # self.assertEqual(ec_user_not_found, data)
        self.assertEqual(200, resp.status_code)
        print data

        # Test: email, ndb objects

        # Valid recipient user
        # Create valid user

        # Email has preference over username if both are passed
        pass


class TestNotifyLocation(test_base.TestCase):

    def setUp(self):
        super(TestNotifyLocation, self).setUp()
        self.client = self.app.test_client()
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
        fixtures.create_user_account(self.client)


class TestUserProfile(test_base.TestCase):

    def setUp(self):
        super(TestUserProfile, self).setUp()
        self.client = self.app.test_client()
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
        fixtures.create_user_account(self.client)


class TestUserActivity(test_base.TestCase):

    def setUp(self):
        super(TestUserActivity, self).setUp()
        self.client = self.app.test_client()
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = lambda(x): UUID
        fixtures.create_user_account(self.client)


if __name__ == '__main__':
    unittest.main()
