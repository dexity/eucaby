
import flask_restful
import datetime
import itertools
import mock
import unittest
import urllib
from flask import json
from flask_oauthlib import client as f_oauth_client
from flask_restful import inputs as fr_inputs

from google.appengine.ext import testbed

from eucaby_api import args
from eucaby_api import fields as api_fields
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
        # Notes:
        #   - I couldn't mock
        #     oauthlib.oauth2.rfc6749.tokens.random_token_generator so I
        #     decided to set the config parameter.
        #   - Patch works when running just this test, it doesn't work when
        #     running all tests. Need to figure out why
        # generator = lambda(x): fixtures.UUID
        # self.app.config['OAUTH2_PROVIDER_TOKEN_GENERATOR'] = generator
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
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        ec_success_resp = dict(
            access_token=data['access_token'],
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=data['refresh_token'],
            scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
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
            access_token=ec_token.access_token,
            refresh_token=ec_token.refresh_token)
        models.Token.query.delete()  # Clean up tokens

        # Test B: Valid token, user exists, fb profile
        fb_params = dict(access_token='anotheraccesstoken')
        self.fb_valid_token.update(fb_params)
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        ec_success_resp.update(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'])
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
            access_token=ec_token.access_token,
            refresh_token=ec_token.refresh_token)
        models.Token.query.delete()

        # Test C: Extra parameters are ignored
        self.valid_params['extra'] = 'param'
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        ec_success_resp.update(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'])
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
        fb_get.side_effect = side_effect
        resp = self.client.post('/oauth/token', data=self.valid_params)
        data = json.loads(resp.data)
        ec_success_resp = dict(
            access_token=data['access_token'],
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=data['refresh_token'],
            scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
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

        resp = self.client.post('/oauth/token', data=valid_params)
        data = json.loads(resp.data)
        ec_success_resp = dict(
            access_token=data['access_token'],
            expires_in=self.app.config['OAUTH2_PROVIDER_TOKEN_EXPIRES_IN'],
            refresh_token=data['refresh_token'],
            scope=' '.join(models.EUCABY_SCOPES),
            token_type=fixtures.TOKEN_TYPE)
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
        self.user = fixtures.create_user()

    @mock.patch('eucaby_api.auth.facebook._tokengetter')
    def test_general_errors(self, fb_tokengetter):
        """Tests general errors."""
        # Note: Some of the tests are general to all oauth requests
        # Test A: No token is passed
        resp = self.client.get('/friends')
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
        self.assertEqual(401, resp.status_code)

        # Test B: Invalid Eucaby token
        resp = self.client.get(
            '/friends', headers=dict(Authorization='Bearer {}'.format('wrong')))
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
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
        self.assertEqual(fixtures.INVALID_TOKEN, data)
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
        self.assertEqual(fixtures.INVALID_TOKEN, data)
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
        self.user2 = fixtures.create_user2()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def _verify_data_email(
            self, resp, recipient_username, recipient_name, recipient_email,
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
        session = req.session

        # Check response
        ec_valid_data = dict(data=dict(
            id=req.id, type='request',
            recipient=dict(
                username=recipient_username, name=recipient_name,
                email=recipient_email),
            sender=dict(username=self.user.username, name=self.user.name),
            created_date=fr_inputs.iso8601(req.created_date),
            session=dict(key=session.key, complete=False)))
        self.assertEqual(ec_valid_data, data)
        self.assertEqual(200, resp.status_code)
        # Check email content
        messages = self.mail_stub.get_sent_messages()
        test_utils.verify_email(
            messages, 1, recipient_email, in_list + [req.session.key, ])

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        test_utils.verify_invalid_methods(
            self.client, ['get'], '/location/request')

        # No token is passed
        resp = self.client.post('/location/request')
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
        self.assertEqual(401, resp.status_code)

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
        self._verify_data_email(resp, None, None, recipient_email,
                                ['from Test User', 'Join Eucaby'])

    def test_existing_email(self):
        """Tests valid existing email address."""
        recipient_email = 'test2@example.com'
        resp = self.client.post(
            '/location/request', data=dict(email=recipient_email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user2.username, self.user2.name, recipient_email,
            ['Hi, Test2 User2', 'from Test User'])

    def test_self_email(self):
        """Test that user can send email to himself."""
        recipient_email = 'test@example.com'
        resp = self.client.post(
            '/location/request', data=dict(email=recipient_email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user.username, self.user.name, recipient_email,
            ['Hi, Test User', 'from Test User'])

    def test_user(self):
        """Tests valid recipient user."""
        resp = self.client.post(
            '/location/request', data=dict(username=self.user2.username),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user2.username, self.user2.name, self.user2.email,
            ['Hi, Test2 User2', 'from Test User'])

    def test_email_user(self):
        """Tests email and username parameters."""
        recipient_email = 'testnew@example.com'
        resp = self.client.post(
            '/location/request', data=dict(
                email=recipient_email, username=self.user2.username),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(resp, None, None, recipient_email,
                                ['from Test User', 'Join Eucaby'])


class TestRequestById(test_base.TestCase):

    def setUp(self):
        super(TestRequestById, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.user2 = fixtures.create_user2()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        test_utils.verify_invalid_methods(
            self.client, ['post'], '/location/request/123')

        # No token is passed
        resp = self.client.get('/location/request/123')
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
        self.assertEqual(401, resp.status_code)

        # Id is not integer
        resp = self.client.get('/location/request/abc')
        data = json.loads(resp.data)
        self.assertIn('Not found', data['message'])
        self.assertEqual(404, resp.status_code)

        # Request is not found
        resp = self.client.get(
            '/location/request/123',
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        not_found = dict(message='Location request not found', code='not_found')
        self.assertEqual(not_found, data)

        # user places request to a new email address
        req = ndb_models.LocationRequest.create(
            self.user.username, self.user.name, None, None,
            'testnew@example.com')
        req_id = req.key.id()

        # user2 is not authorized: neither sender or recipient
        resp = self.client.get(
            '/location/request/{}'.format(req_id),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID2)))
        data = json.loads(resp.data)
        auth_error = dict(
            message='Not authorized to access the data', code='auth_error')
        self.assertEqual(auth_error, data)

    def test_success(self):
        """Tests successful response."""
        # Create request with two notifications
        req = ndb_models.LocationRequest.create(
            self.user.username, self.user.name, self.user2.username,
            self.user.name)
        req_id = req.key.id()
        for latlng in ['11,-11', '22,-22']:
            self.client.post(
                '/location/notification', data=dict(
                    latlng=latlng, key=req.session.key),
                headers=dict(
                    Authorization='Bearer {}'.format(fixtures.UUID2)))

        # User is request sender or request recipient
        for access_token in [fixtures.UUID, fixtures.UUID2]:
            resp = self.client.get(
                '/location/request/{}'.format(req_id),
                headers=dict(Authorization='Bearer {}'.format(access_token)))
            data = json.loads(resp.data)
            self.validate_request(req_id, data)

    def validate_request(self, req_id, data):
        """Validate request with two notifications."""
        username2 = self.user2.username
        notifications = data['notifications']
        self.assertEqual(self.user.username, data['sender']['username'])
        self.assertEqual(req_id, data['id'])
        self.assertEqual(2, len(notifications))
        self.assertFalse('session' in notifications[0])
        self.assertEqual(
            [dict(lat=22, lng=-22), dict(lat=11, lng=-11)],
            [notif['location'] for notif in notifications])
        self.assertEqual(
            [username2, username2],
            [notif['sender']['username'] for notif in notifications])


class TestNotifyLocation(test_base.TestCase):

    def setUp(self):
        super(TestNotifyLocation, self).setUp()
        self.client = self.app.test_client()
        self.user = fixtures.create_user()
        self.user2 = fixtures.create_user2()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def _verify_data_email(
            self, resp, recipient_username, recipient_name, recipient_email,
            in_list, session_dict=None):
        """Validates data and email sending."""
        data = json.loads(resp.data)
        # Check ndb objects
        loc_notif = ndb_models.LocationNotification.query()
        session = ndb_models.Session.query()
        self.assertEqual(1, loc_notif.count())
        self.assertEqual(1, session.count())
        loc_notif = loc_notif.fetch(1)[0]
        session = loc_notif.session
        location = loc_notif.location
        session_out = dict(key=session.key, complete=False)
        if session_dict:
            session_out.update(session_dict)

        # For complete session check the request
        if session_out['complete']:
            req_class = ndb_models.LocationRequest
            loc_req = req_class.query(
                req_class.session == ndb_models.Session(
                    key=session.key)).fetch(1)[0]
            self.assertEqual(session.key, loc_req.session.key)
            # Session should also be complete
            self.assertTrue(loc_req.session.complete)

        # Check response
        ec_valid_data = dict(data=dict(
            id=loc_notif.id, type='notification',
            location=dict(lat=location.lat, lng=location.lon),
            recipient=dict(
                username=recipient_username, name=recipient_name,
                email=recipient_email),
            sender=dict(username=self.user.username, name=self.user.name),
            created_date=fr_inputs.iso8601(loc_notif.created_date),
            session=session_out))
        self.assertEqual(ec_valid_data, data)
        self.assertEqual(200, resp.status_code)
        messages = self.mail_stub.get_sent_messages()
        if len(messages) == 2:
            messages.pop(0)  # Don't need the first message
        test_utils.verify_email(
            messages, 1, recipient_email, in_list + [
                'https://www.google.com/maps/place/{},{}'.format(
                    location.lat, location.lon)])

    def test_general_errors(self):
        """Tests general errors."""
        # Invalid method
        test_utils.verify_invalid_methods(
            self.client, ['get'], '/location/notification')

        # No token is passed
        resp = self.client.post('/location/notification')
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
        self.assertEqual(401, resp.status_code)

        # No parameters
        ec_missing_params = dict(
            message='Invalid request parameters', code='invalid_request',
            fields=dict(latlng='Missing or invalid latlng parameter'))
        resp = self.client.post(
            '/location/notification',
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_missing_params, data)
        self.assertEqual(400, resp.status_code)

        # No key, email or username
        ec_missing_params = dict(
            message='Missing key, email or username parameters',
            code='invalid_request')
        resp = self.client.post(
            '/location/notification', data=dict(latlng=fixtures.LATLNG),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_missing_params, data)
        self.assertEqual(400, resp.status_code)

        # Invalid recipient email address
        ec_invalid_email = dict(
            fields=dict(email='Invalid email'),
            message='Invalid request parameters', code='invalid_request')
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, email='wrong'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(ec_invalid_email, data)
        self.assertEqual(400, resp.status_code)

        # Request not found
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, key='456'),
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

    def test_key(self):
        """Tests notification by session key."""
        # Create request
        # user2 created request to user: user2 -> user
        resp = self.client.post(
            '/location/request', data=dict(email='test@example.com'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID2)))
        data = json.loads(resp.data)
        key = data['data']['session']['key']

        # user notifies user2 to existing request: user --> user2
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, key=key),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        session_dict = dict(complete=True)  # Request is complete
        self.assertEqual(1, ndb_models.LocationRequest.query().count())
        self._verify_data_email(
            resp, self.user2.username, self.user2.name, self.user2.email,
            ['Hi, Test2 User2', 'Test User shared'], session_dict)

        # Idempotent operation: user repeats the operation
        self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, key=key),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self.assertEqual(1, ndb_models.LocationRequest.query().count())
        self.assertEqual(2, ndb_models.LocationNotification.query().count())
        self.assertEqual(1, ndb_models.Session.query().count())

    def test_self_key(self):
        """Tests notification by session key to himself."""
        # Create request
        # user created request to user: user -> user
        resp = self.client.post(
            '/location/request', data=dict(email='test@example.com'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        key = data['data']['session']['key']

        # user notifies himself
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, key=key),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        session_dict = dict(complete=True)  # Request is complete
        self.assertEqual(1, ndb_models.LocationRequest.query().count())
        self._verify_data_email(
            resp, self.user.username, self.user.name, self.user.email,
            ['Hi, Test User', 'Test User shared'], session_dict)

    def test_new_email(self):
        """Tests notification new email."""
        # user --> new email
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, email='test3@example.com'),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, None, None, 'test3@example.com',
            ['Test User shared', 'Join Eucaby'])

    def test_existing_email(self):
        """Tests notification to existing email."""
        # user sends notification to user2: user --> user2
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, email=self.user2.email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user2.username, self.user2.name, self.user2.email,
            ['Hi, Test2 User2', 'Test User shared'])

    def test_self_email(self):
        """Tests notification his own email."""
        # user sends notification to self: user --> user
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, email=self.user.email),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user.username, self.user.name, self.user.email,
            ['Hi, Test User', 'Test User shared'])

    def test_username(self):
        """Tests notification by username."""
        # user notifies user2 to existing request: user --> user2
        resp = self.client.post(
            '/location/notification', data=dict(
                latlng=fixtures.LATLNG, username=self.user2.username),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        self._verify_data_email(
            resp, self.user2.username, self.user2.name, self.user2.email,
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

        # No token is passed
        resp = self.client.get('/me')
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
        self.assertEqual(401, resp.status_code)

    def test_user(self):
        resp = self.client.get(
            '/me', headers=dict(
                Authorization='Bearer {}'.format(fixtures.UUID)))
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
        self.user = fixtures.create_user()
        self.user2 = fixtures.create_user2()
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()

        # Test Cases
        # ----------
        # Reverse order: array is counted from the top
        #
        #    Req         Notif
        #    +----+      +----+       Time  Array
        #    |    |      |    |        6      0
        #    | <- |:----:| -> |        5      1
        # U1 +----+      +----+ U2
        #    |****|      |****|        4      2
        #    |****|      |****|        3      3
        #    +----+      +----+
        #    |    |:----:|    |        2      4
        #    | -> |      | <- |        1      5
        #    |    |      |    |        0      6
        #    +----+      +----+
        #
        # Comment notations:
        # ------------------
        # > sent to U2
        # ] sent to U2 and complete
        # * sent to email
        # [ received from U2 and complete
        # < received from U2

        self.requests = self._create_requests()
        self._create_notifications()
        self.notifications = ndb_models.LocationNotification.query().fetch()
        self._adjust_timeline()

    def tearDown(self):
        self.testbed.deactivate()

    @classmethod
    def _create_params(cls, user1, user2):
        params = []
        # username1 sends 3 requests or notifications to username2
        params += list(itertools.repeat(
            [user1.username, user1.name, user2.username, user2.name, None], 3))
        # username1 sends 2 requests or notifications to new emails
        params += [[user1.username, user1.name, None, None,
                    'testnew{}@example.com'.format(i)]
                   for i in range(2)]
        # username2 sends 2 requests or notifications to username1
        params += list(itertools.repeat(
            [user2.username, user2.name, user1.username, user1.name, None], 2))
        return params

    def _adjust_timeline(self):
        """Adjusts timeline for requests and notifications."""
        # Set notification 6 before requests
        notif6 = self.notifications[6]
        new_created_date = notif6.created_date - datetime.timedelta(minutes=1)
        notif6.created_date = new_created_date
        notif6.put()
        # Set request 6 after notifications
        req6 = self.requests[6]
        new_created_date = req6.created_date + datetime.timedelta(minutes=1)
        req6.created_date = new_created_date
        req6.put()

    def _create_requests(self):
        """Creates requests."""
        params = self._create_params(self.user, self.user2)
        requests = []
        # Create requests
        for param in params:
            req = ndb_models.LocationRequest.create(*param)
            requests.append(req)
        return requests

    def _create_notifications(self):
        """Creates notifications."""
        params = self._create_params(self.user2, self.user)
        latlngs = ['0,0', '11,-11', '22,-22', '33,-33', '44,-44', '55,-55',
                   '66,-66']
        for i in range(7):
            if i in [2, 5]:
                # notif2 (from user2) -> req2 (to user)
                bearer_token = fixtures.UUID2
                if i == 5:  # notif5 (from user) -> req5 (to user2)
                    bearer_token = fixtures.UUID
                self.client.post(
                    '/location/notification', data=dict(
                        latlng=latlngs[i],
                        key=self.requests[i].session.key),
                    headers=dict(
                        Authorization='Bearer {}'.format(bearer_token)))
                continue
            ndb_models.LocationNotification.create(latlngs[i], *params[i])

    def test_general_errors(self):
        """Tests general errors."""
        # No token is passed
        resp = self.client.get('/history')
        data = json.loads(resp.data)
        self.assertEqual(fixtures.INVALID_TOKEN, data)
        self.assertEqual(401, resp.status_code)

        # Invalid method
        test_utils.verify_invalid_methods(self.client, ['post'], '/history')

        # Invalid activity type
        invalid_request = dict(
            fields=dict(type=args.INVALID_ACTIVITY_TYPE),
            message='Invalid request parameters', code='invalid_request')
        params = urllib.urlencode(dict(type='wrong'))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(invalid_request, data)
        self.assertEqual(400, resp.status_code)

        # Invalid offset or limit
        invalid_request = dict(
            fields=dict(offset=args.INVALID_INT, limit=args.INVALID_INT),
            message='Invalid request parameters', code='invalid_request')
        params = urllib.urlencode(dict(type='outgoing', offset='a', limit='b'))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(invalid_request, data)
        self.assertEqual(400, resp.status_code)

        # Negative offset or limit
        params = urllib.urlencode(dict(type='outgoing', offset=-1, limit=-2))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(invalid_request, data)
        self.assertEqual(400, resp.status_code)

    def test_history_request(self):
        """Tests request activity type.

        time:       0 1 2 3 4 5 6
        requests:   0 1 2 3 4 5 6
        data:       4 3 2 1 0 - -
                    > > ] * * [ <
        """
        params = urllib.urlencode(dict(type='request'))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(5, len(data['data']))
        for i in range(5):
            req = json.dumps(flask_restful.marshal(
                self.requests[i], api_fields.REQUEST_FIELDS))
            self.assertEqual(req, json.dumps(data['data'][4-i]))
        # Complete requests
        self.assertTrue(data['data'][2]['session']['complete'])
        # Request to new email is never complete
        self.assertFalse(data['data'][3]['session']['complete'])

    def test_history_notification(self):
        """Tests notification activity type.

        time:           0 1 2 3 4 5 6
        notifications:  6 0 1 2 3 4 5   # moved notif 6 as earliest
        data:           1 - - - - - 0
                        > - - - - - ]
        """
        params = urllib.urlencode(dict(type='notification'))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(2, len(data['data']))
        for i in range(2):
            notif = json.dumps(flask_restful.marshal(
                self.notifications[5+i], api_fields.NOTIFICATION_FIELDS))
            self.assertEqual(notif, json.dumps(data['data'][i]))
        # Complete notifications
        self.assertTrue(data['data'][0]['session']['complete'])
        # Notification hasn't been complete
        self.assertFalse(data['data'][1]['session']['complete'])

    def test_history_outgoing(self):
        """Tests outgoing activity type.

        time:           0  1  2  3  4  5  6  7  8  9  10 11 12 13
        requests:          0  1  2  3  4  5                    6
                           r> r> r] r* r* -                    -
        notifications:  6                    0  1  2  3  4  5
                        n>                   -  -  -  -  -  n]
        data:           6  5  4  3  2  1  0  # not in time scale
                        n> r> r> r] r* r* n]
        """
        params = urllib.urlencode(dict(type='outgoing'))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(7, len(data['data']))
        # Check types
        notif, req = 'notification', 'request'
        expected_types = [notif, req, req, req, req, req, notif]
        self.assertEqual(expected_types, [x['type'] for x in data['data']])
        # Check first element from data
        notif = json.dumps(flask_restful.marshal(
            self.notifications[6], api_fields.NOTIFICATION_FIELDS))
        self.assertEqual(notif, json.dumps(data['data'][6]))
        # Check completeness
        self.assertFalse(data['data'][6]['session']['complete'])
        self.assertTrue(data['data'][3]['session']['complete'])
        self.assertTrue(data['data'][0]['session']['complete'])

    def test_history_incoming(self):
        """Tests incoming activity type.

        time:           0  1  2  3  4  5  6  7  8  9  10 11 12 13
        requests:          0  1  2  3  4  5                    6
                           -  -  -  -  -  r[                   r<
        notifications:  6                    0  1  2  3  4  5
                        -                    n< n< n[ -  -  -
        data:           4  3  2  1  0  # not in time scale
                        r[ n< n< n[ r<
        """
        params = urllib.urlencode(dict(type='incoming'))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(5, len(data['data']))
        # Check types
        notif, req = 'notification', 'request'
        expected_types = [req, notif, notif, notif, req]
        self.assertEqual(expected_types, [x['type'] for x in data['data']])
        # Check first element from data
        req = json.dumps(flask_restful.marshal(
            self.requests[6], api_fields.REQUEST_FIELDS))
        self.assertEqual(req, json.dumps(data['data'][0]))
        # Check completeness
        self.assertTrue(data['data'][1]['session']['complete'])
        self.assertTrue(data['data'][4]['session']['complete'])
        self.assertFalse(data['data'][0]['session']['complete'])

    def test_offset_limit(self):
        """Tests offset and limit."""
        # Offset larger the number of request
        params = urllib.urlencode(dict(type='request', offset=10))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual([], data['data'])

        # There are no gaps in returned list
        # time:       0 1 2 3 4 5 6
        # requests:   0 1 2 3 4 5 6
        # data:       4 3|2 1|0 - -
        #             > >|] *|* [ <
        requests = []
        next_offset = 1
        for i in range(1, 3):  # border between user and email requests   # pylint: disable=unused-variable
            params = urllib.urlencode(
                dict(type='request', offset=next_offset, limit=1))
            resp = self.client.get(
                '/history?{}'.format(params),
                headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
            data = json.loads(resp.data)
            next_offset = data['paging']['next_offset']  # update next_offset
            requests.append(data['data'][0])
        req2 = json.dumps(flask_restful.marshal(
            self.requests[2], api_fields.REQUEST_FIELDS))
        req3 = json.dumps(flask_restful.marshal(
            self.requests[3], api_fields.REQUEST_FIELDS))
        self.assertEqual(req3, json.dumps(requests[0]))  # user -> new email
        self.assertEqual(req2, json.dumps(requests[1]))  # user -> user2

        # Offset and limit for outgoing
        # data: |6  5  4  3  2 |1  0
        #       |n> r> r> r] r*|r* n]
        params = urllib.urlencode(
            dict(type='outgoing', offset=2, limit=5))
        resp = self.client.get(
            '/history?{}'.format(params),
            headers=dict(Authorization='Bearer {}'.format(fixtures.UUID)))
        data = json.loads(resp.data)
        self.assertEqual(5, len(data['data']))
        # Check types
        notif, req = 'notification', 'request'
        expected_types = [req, req, req, req, notif]
        self.assertEqual(expected_types, [x['type'] for x in data['data']])


if __name__ == '__main__':
    unittest.main()
