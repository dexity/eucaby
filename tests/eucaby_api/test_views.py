import unittest
from flask import json
import mock
from eucaby_api import auth
from eucaby_api import wsgi

class TestViews(unittest.TestCase):

    def setUp(self):
        app = wsgi.create_app()
        app.config.from_object('eucaby_api.config.Testing')
        self.app = app.test_client()
        self.grant_password_error = dict(
            code="invalid",
            fields=dict(
                grant_type="Valid grant types are password and refresh_token",
                password="Missing required parameter password",
                service="Invalid service",
                username="Missing required parameter username"
            ),
            message="Invalid request parameters"
        )

    def tearDown(self):
        pass

    @mock.patch('eucaby_api.auth.facebook.exchange_token')
    def testExchangeToken(self, ex_token):
        # Get is not supported
        resp = self.app.get('/oauth/token')
        self.assertEqual(405, resp._status_code)

        # No parameters
        resp = self.app.post('/oauth/token')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(400, resp._status_code)
        data = json.loads(resp.data)
        self.assertEqual(data, self.grant_password_error)

        # Invalid grant type
        resp = self.app.post('/oauth/token', dict(grant_type='wrong'))
        self.assertEqual(400, resp._status_code)
        self.assertEqual(data, self.grant_password_error)

        # Grant type is set
        resp = self.app.post('/oauth/token', data=dict(grant_type='password'))
        data = json.loads(resp.data)
        assert_data = self.grant_password_error.copy()
        assert_data['fields'].pop('grant_type')
        self.assertEqual(data, assert_data)

        # All parameters are set
        params = dict(grant_type='password', service='facebook',
                    password='test_password', username='test_username')
        # # XXX: Finish
        # # Valid token
        # ex_token.return_value = dict(access_token='someaccesstoken',
        #                              expires=123)
        # resp = self.app.post('/oauth/token', data=params)

        message = 'Invalid OAuth access token.'
        ex_token.side_effect = auth.f_oauth_client.OAuthException(message)
        resp = self.app.post('/oauth/token', data=params)
        data = json.loads(resp.data)
        self.assertEqual(data, dict(code='invalid_oauth', message=message))

        # Expired token
        # ex_token




        data = json.loads(resp.data)

        # XXX: Finish
        #params['extra'] = 'param'
        # Short-lived token
        print resp.data


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
