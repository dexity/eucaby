
import datetime
import mock
import unittest
from flask import json
from flask_oauthlib import client as f_oauth_client
from flask_restful import inputs as fr_inputs

from google.appengine.ext import testbed

from eucaby_api import models
from eucaby_api import ndb_models

from tests.eucaby_api import base as test_base
from tests.eucaby_api import fixtures
from tests.utils import utils as test_utils


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
        generator = lambda(x): fixtures.UUID
        self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = generator
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
        fb_exchange_token.side_effect = f_oauth_client.OAuthException(
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
        fb_get.return_value = mock.Mock(data=fixtures.FB_PROFILE)
        ec_success_resp = dict(
            access_token=fixtures.UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=fixtures.UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
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
            access_token=fixtures.UUID, refresh_token=fixtures.UUID)
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
            access_token=fixtures.UUID, refresh_token=fixtures.UUID)
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
        side_effect = f_oauth_client.OAuthException(
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
        fb_get.return_value = mock.Mock(data=fixtures.FB_PROFILE)
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
            access_token=fixtures.UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=fixtures.UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
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
        fb_get.return_value = mock.Mock(data=fixtures.FB_PROFILE)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        refresh_token = data['refresh_token']

        # Valid refresh token
        # Note: I tried to change token generator to return UUID2 but
        #   server method is being cached and I couldn't change it
        valid_params = dict(
            grant_type='refresh_token', refresh_token=refresh_token)
        ec_success_resp = dict(
            access_token=fixtures.UUID,
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=fixtures.UUID, scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)

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
        fixtures.create_user()

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
            '/friends', headers=dict(
                Authorization='Bearer {}'.format(fixtures.UUID)))
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
                    Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_service_error, data)
        self.assertEqual(401, resp.status_code)

        # Test E: Eucaby token expired
        ec_token = models.Token.query.filter_by(service=models.EUCABY)[0]
        ec_token.expires = ec_token.expires - datetime.timedelta(days=31)
        self.app.db.session.add(ec_token)
        self.app.db.session.commit()
        resp = self.client.get(
            '/friends', headers=dict(
                Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_unauthorized_error, data)
        self.assertEqual(401, resp.status_code)

        # Test F: User is not active
        ec_token.expires = datetime.datetime.now() + datetime.timedelta(days=30)
        ec_token.user.is_active = False
        self.app.db.session.add(ec_token)
        self.app.db.session.commit()
        resp = self.client.get(
            '/friends', headers=dict(
                Authorization='Bearer {}'.format(fixtures.UUID)))
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
            '/friends', headers=dict(
                Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_resp, data)
        self.assertEqual(200, resp.status_code)

        # Empty list of friends
        fb_friends['data'] = []
        fb_request.return_value = mock.Mock(data=fb_friends, status=200)
        resp = self.client.get(
            '/friends', headers=dict(
                Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(dict(data=[]), data)
        self.assertEqual(200, resp.status_code)


class TestRequestLocation(test_base.TestCase):

    def setUp(self):
        super(TestRequestLocation, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.user2 = fixtures.create_user(
            user_kwargs=dict(username='3456', first_name='Test2',
                             last_name='User2', email='test2@example.com'),
            ec_token_kwargs=dict(access_token='111', refresh_token='222'),
            fb_access_token='someaccesstoken2')
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def _verify_data_email(self, resp, recipient_username, recipient_email,
                           in_list):
        """Validates data and email sending."""
        # Assume that request is made by self.user
        data = json.loads(resp.data)
        # Check ndb objects
        req = ndb_models.LocationRequest.query()
        session = ndb_models.Session.query()
        self.assertEqual(1, req.count())
        self.assertEqual(1, session.count())
        req = req.fetch(1)[0]
        session = session.fetch(1)[0]

        # Check response
        ec_valid_email = dict(data=dict(
            id=req.id, token=req.token, type='request',
            created_date=fr_inputs.iso8601(req.created_date),
            session=dict(
                recipient_username=recipient_username,
                sender_username=self.user.username, key=session.key,
                recipient_email=recipient_email)))
        self.assertEqual(ec_valid_email, data)
        self.assertEqual(200, resp.status_code)
        # Check email content
        messages = self.mail_stub.get_sent_messages()
        test_utils.verify_email(
            messages, 1, recipient_email, in_list + [req.token, ])

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        test_utils.verify_invalid_methods(
            self.client, ['get'], '/location/request')

        # No parameters
        ec_missing_params = dict(
            message='Missing email or username parameters',
            code='invalid_request')
        resp = self.client.post(
            '/location/request',
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_missing_params, data)
        self.assertEqual(400, resp.status_code)

        # Invalid recipient email address
        ec_invalid_email = dict(
            fields=dict(email='Invalid email'),
            message='Invalid request parameters', code='invalid_request')
        resp = self.client.post(
            '/location/request', data=dict(email='wrong'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_invalid_email, data)
        self.assertEqual(400, resp.status_code)

        # Invalid recipient (not found or inactive)
        resp = self.client.post(
            '/location/request', data=dict(username='456'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        ec_user_not_found = dict(message='User not found', code='not_found')
        self.assertEqual(ec_user_not_found, data)
        self.assertEqual(404, resp.status_code)

    def test_new_email(self):
        """Tests valid new email address."""
        recipient_email = 'testnew@example.com'
        resp = self.client.post(
            '/location/request', data=dict(email=recipient_email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(resp, None, recipient_email,
                                ['from Test User', 'Join Eucaby'])

    def test_existing_email(self):
        """Tests valid existing email address."""
        recipient_email = 'test2@example.com'
        resp = self.client.post(
            '/location/request', data=dict(email=recipient_email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(resp, self.user2.username, recipient_email,
                                ['Hi, Test2 User2', 'from Test User'])

    def test_self_email(self):
        """Test that user can send email to himself."""
        recipient_email = 'test@example.com'
        resp = self.client.post(
            '/location/request', data=dict(email=recipient_email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(resp, self.user.username, recipient_email,
                                ['Hi, Test User', 'from Test User'])

    def test_user(self):
        """Tests valid recipient user."""
        resp = self.client.post(
            '/location/request', data=dict(username=self.user2.username),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(resp, self.user2.username, self.user2.email,
                                ['Hi, Test2 User2', 'from Test User'])

    def test_email_user(self):
        """Tests email and username parameters."""
        recipient_email = 'testnew@example.com'
        resp = self.client.post(
            '/location/request', data=dict(
                email=recipient_email, username=self.user2.username),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(resp, None, recipient_email,
                                ['from Test User', 'Join Eucaby'])


class TestNotifyLocation(test_base.TestCase):

    def setUp(self):
        super(TestNotifyLocation, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.user2 = fixtures.create_user(
            user_kwargs=dict(username='3456', first_name='Test2',
                             last_name='User2', email='test2@example.com'),
            ec_token_kwargs=dict(
                access_token=fixtures.UUID2, refresh_token='222'),
            fb_access_token='someaccesstoken2')
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def _verify_data_email(self, resp, recipient_username, recipient_email,
                           in_list, session_dict=None):
        """Validates data and email sending."""
        data = json.loads(resp.data)
        # Check ndb objects
        loc_resp = ndb_models.LocationResponse.query()
        session = ndb_models.Session.query()
        self.assertEqual(1, loc_resp.count())
        self.assertEqual(1, session.count())
        loc_resp = loc_resp.fetch(1)[0]
        session = session.fetch(1)[0]
        lat, lng = loc_resp.location.lat, loc_resp.location.lon
        session_out = dict(
            recipient_username=recipient_username,
            sender_username=self.user.username,
            key=session.key, recipient_email=recipient_email)
        if session_dict:
            session_out.update(session_dict)
        # Check response
        ec_valid_email = dict(data=dict(
            id=loc_resp.id, type='notification', lat=lat, lng=lng,
            created_date=fr_inputs.iso8601(loc_resp.created_date),
            session=session_out))
        self.assertEqual(ec_valid_email, data)
        self.assertEqual(200, resp.status_code)
        messages = self.mail_stub.get_sent_messages()
        if len(messages) == 2:
            messages.pop(0)  # Don't need the first message
        test_utils.verify_email(
            messages, 1, recipient_email, in_list + [
                'https://www.google.com/maps/place/{},{}'.format(lat, lng)])

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        test_utils.verify_invalid_methods(
            self.client, ['get'], '/location/notify')

        # No parameters
        ec_missing_params = dict(
            message='Invalid request parameters', code='invalid_request',
            fields=dict(latlng='Missing or invalid latlng parameter'))
        resp = self.client.post(
            '/location/notify',
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_missing_params, data)
        self.assertEqual(400, resp.status_code)

        # No request_token, email or username
        ec_missing_params = dict(
            message='Missing request_token, email or username parameters',
            code='invalid_request')
        resp = self.client.post(
            '/location/notify', data=dict(latlng=fixtures.LATLNG),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_missing_params, data)
        self.assertEqual(400, resp.status_code)

        # Invalid recipient email address
        ec_invalid_email = dict(
            fields=dict(email='Invalid email'),
            message='Invalid request parameters', code='invalid_request')
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, email='wrong'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_invalid_email, data)
        self.assertEqual(400, resp.status_code)

        # Request not found
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, request_token='456'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        ec_user_not_found = dict(message='Request not found', code='not_found')
        self.assertEqual(ec_user_not_found, data)
        self.assertEqual(404, resp.status_code)

        # Invalid recipient (not found or inactive)
        resp = self.client.post(
            '/location/request', data=dict(
                latlng=fixtures.LATLNG, username='456'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        ec_user_not_found = dict(message='User not found', code='not_found')
        self.assertEqual(ec_user_not_found, data)
        self.assertEqual(404, resp.status_code)

    def test_request_token(self):
        """Tests notification by request token."""
        # Create request
        # user2 created request to user: user2 -> user
        resp = self.client.post(
            '/location/request', data=dict(email='test@example.com'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID2)))
        data = json.loads(resp.data)
        request_token = data['data']['token']
        # user notifies user2 to existing request: user --> user2
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, request_token=request_token),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))

        # Recipient and sender are opposite because notification is a
        # response to the request
        session_dict = dict(
            recipient_username=self.user.username,
            sender_username=self.user2.username,
            recipient_email='test@example.com')

        self.assertEqual(1, ndb_models.LocationRequest.query().count())
        self._verify_data_email(
            resp, self.user2.username, self.user2.email,
            ['Hi, Test2 User2', 'Test User shared'], session_dict)

        # Idempotent operation
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, request_token=request_token),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self.assertEqual(1, ndb_models.LocationRequest.query().count())
        self.assertEqual(2, ndb_models.LocationResponse.query().count())
        self.assertEqual(1, ndb_models.Session.query().count())

    def test_new_email(self):
        """Tests notification new email."""
        # user --> new email
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, email='test3@example.com'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, None, 'test3@example.com',
            ['Test User shared', 'Join Eucaby'])

    def test_existing_email(self):
        """Tests notification to existing email."""
        # user sends notification to user2: user --> user2
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, email=self.user2.email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user2.username, self.user2.email,
            ['Hi, Test2 User2', 'Test User shared'])

    def test_self_email(self):
        """Tests notification his own email."""
        # user sends notification to self: user --> user
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, email=self.user.email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user.username, self.user.email,
            ['Hi, Test User', 'Test User shared'])

    def test_username(self):
        """Tests notification by username."""
        # user notifies user2 to existing request: user --> user2
        resp = self.client.post(
            '/location/notify', data=dict(
                latlng=fixtures.LATLNG, username=self.user2.username),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user2.username, self.user2.email,
            ['Hi, Test2 User2', 'Test User shared'])


class TestUserProfile(test_base.TestCase):

    def setUp(self):
        super(TestUserProfile, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        test_utils.verify_invalid_methods(self.client, ['post'], '/me')

    def test_user(self):
        resp = self.client.get('/me',
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        ec_valid_resp = dict(
            data=dict(
                username=self.user.username, first_name=self.user.first_name,
                last_name=self.user.last_name, gender=self.user.gender,
                email=self.user.email,
                date_joined=fr_inputs.iso8601(self.user.date_joined)))
        self.assertEqual(ec_valid_resp, data)


class TestUserActivity(test_base.TestCase):

    def setUp(self):
        super(TestUserActivity, self).setUp()
        self.client = self.app.test_client()
        fixtures.create_user()


if __name__ == '__main__':
    unittest.main()
