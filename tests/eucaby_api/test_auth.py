import json
import mock
import unittest
from eucaby_api import wsgi
from eucaby_api import auth

class FacebookRemoteAppTest(unittest.TestCase):

    def setUp(self):
        self.app = wsgi.create_app()
        self.app.config.from_object('eucaby_api.config.Testing')
        self.app.secret_key = 'development'
        self.facebook = auth.facebook

    @mock.patch('flask_oauthlib.client.parse_response')
    @mock.patch('eucaby_api.auth.FacebookRemoteApp.http_request')
    def test_fb_exchange_token(self, http_req, parse_resp):
        # Success
        resp = mock.Mock()
        resp.code = 200
        data = dict(access_token='someaccesstoken', expires=123)
        content = json.dumps(data)
        http_req.return_value = resp, content
        parse_resp.return_value = data
        resp = self.facebook.exchange_token('sl_token')
        self.assertEqual(resp, data)

        # Invalid token
        resp = mock.Mock()
        resp.code = 403
        data = dict(error=dict(message='Invalid OAuth access token.',
                               type='OAuthException', code=190))
        content = json.dumps(data)
        http_req.return_value = resp, content
        parse_resp.return_value = data
        self.assertRaises(auth.f_oauth_client.OAuthException,
                          self.facebook.exchange_token, 'sl_token')


if __name__ == "__main__":
    unittest.main()
