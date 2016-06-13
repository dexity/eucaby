# -*- coding: utf-8 -*-
"""Tests authentication module."""

import flask
import json
import unittest

import mock
from eucaby_api import auth
from eucaby_api import models
from eucaby_api import app as eucaby_app

from tests.eucaby_api import base as test_base


class FacebookRemoteAppTest(unittest.TestCase):

    def setUp(self):
        self.app = eucaby_app.create_app()
        self.app.config.from_object(test_base.Testing)
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


class AuthTest(test_base.TestCase):

    def setUp(self):
        super(AuthTest, self).setUp()
        self.app = eucaby_app.create_app()
        self.app.config.from_object(test_base.Testing)
        self.app.secret_key = 'development'
        self.user = models.User.create(
            username='2345', first_name='Test', last_name=u'Юзер',
            email='test@example.com')

    def test_eucaby_tokengetter(self):
        """Tests Eucaby token getter."""
        params = dict(access_token='1', expires_in=5, scope='',
                      refresh_token='2')
        token = models.Token.create_eucaby_token(self.user.id, params)
        # No token
        self.assertIsNone(auth.eucaby_tokengetter())
        # Token doesn't exist
        self.assertIsNone(auth.eucaby_tokengetter(access_token='3'))
        # Token by access token
        with self.app.test_request_context('/'):
            ec_token = auth.eucaby_tokengetter(access_token='1')
            self.assertEqual(token, ec_token)
            ec_token = auth.eucaby_tokengetter(refresh_token='2')
            self.assertEqual(token, ec_token)

    def test_facebook_tokengetter(self):
        """Tests FB token getter."""
        params = dict(user_id=self.user.id, access_token='1',
                      expires_seconds=5)
        token = models.Token.create_facebook_token(**params)
        with self.app.test_request_context('/'):
            flask.request.user = None
            # No token
            self.assertIsNone(auth.facebook_tokengetter())
            # Token exists
            flask.request.user = self.user
            token_list = auth.facebook_tokengetter()
            self.assertEqual(token.access_token, token_list[0])


if __name__ == '__main__':
    unittest.main()
