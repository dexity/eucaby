import unittest
from flask import json
import mock
from eucaby_api import auth
from eucaby_api import wsgi

class TestOAuthToken(unittest.TestCase):

    def setUp(self):
        app = wsgi.create_app()
        app.config.from_object('eucaby_api.config.Testing')
        self.app = app.test_client()
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
        self.invalid_grant = dict(
            code='invalid_grant',
            fields=dict(
                grant_type='Valid grant types are password and refresh_token'
            ),
            message='Invalid request parameters'
        )

    def tearDown(self):
        pass

    def testGeneralErrors(self):
        """Tests general errors related to oauth."""
        # Get is not supported
        resp = self.app.get('/oauth/token')
        self.assertEqual(405, resp._status_code)

        # No parameters
        resp = self.app.post('/oauth/token')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(400, resp._status_code)
        data = json.loads(resp.data)
        self.assertEqual(self.invalid_grant, data)

        # Invalid grant type
        resp = self.app.post('/oauth/token', dict(grant_type='wrong'))
        self.assertEqual(400, resp._status_code)
        self.assertEqual(self.invalid_grant, data)

    @mock.patch('eucaby_api.auth.facebook.get')
    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def testExchangeToken(self, fb_exchange_token, fb_get):
        # Grant type is set
        resp = self.app.post('/oauth/token', data=dict(grant_type='password'))
        data = json.loads(resp.data)
        assert_data = self.grant_password_error.copy()
        assert_data['fields'].pop('grant_type')
        self.assertEqual(assert_data, data)

        # All parameters are set
        params = dict(grant_type='password', service='facebook',
                      password='test_password', username='test_username')
        # Valid token, user doesn't exist
        fb_exchange_token.return_value = dict(
            access_token='someaccesstoken', expires=123)
        # fb_get.return_value = {u'first_name': u'Alexander', u'last_name': u'Dementsov', u'verified': True, u'name': u'Alexander Dementsov', u'locale': u'en_US', u'gender': u'male', u'email': u'dexity@gmail.com', u'link': u'https://www.facebook.com/app_scoped_user_id/10152815532718638/', u'timezone': -8, u'updated_time': u'2014-12-06T21:31:50+0000', u'id': u'10152815532718638'}
        # resp = self.app.post('/oauth/token', data=params)

        # Valid token, user doesn't exist, fb profile error

        # Valid token, user exists

        # message = 'Invalid OAuth access token.'
        # ex_token.side_effect = auth.f_oauth_client.OAuthException(message)
        # resp = self.app.post('/oauth/token', data=params)
        # data = json.loads(resp.data)
        # self.assertEqual(403, resp._status_code)
        # self.assertEqual(dict(code='invalid_oauth', message=message), data)


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
        # resp = self.app.post('/oauth/token', dict(grant_type='refresh_token'))
        #


    def testRefreshToken(self):

        # # Invalid refresh token
        #
        # print resp._status_code
        # print resp.data

        # resp = self.app.post(
        #     '/oauth/token', data=dict(
        #         service='facebook', grant_type='password', username='test_user',
        #         password='test_token'))
        # self.assertEqual(200, resp._status_code)
        # # XXX: Add Facebook mock
        pass


    def testAuthRequest(self):
        pass


if __name__ == "__main__":
    unittest.main()
