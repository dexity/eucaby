"""Authentication module."""

import flask
from flask import json
import functools
from flask_oauthlib import client as f_oauth_client
from flask_oauthlib import provider
from oauthlib import common as oauth_common
from oauthlib import oauth2 as oauth_oauth2

from eucaby_api import models
from eucaby_api.utils import utils as api_utils

oauth = f_oauth_client.OAuth()  # Client for remote APIs

GRANT_TYPE_PASSWORD = 'password'
GRANT_TYPE_REFRESH = 'refresh_token'
GRANT_TYPE_CHOICES = [GRANT_TYPE_PASSWORD, GRANT_TYPE_REFRESH]


class FacebookRemoteApp(f_oauth_client.OAuthRemoteApp):

    """Facebook remote app."""

    def __init__(self, oauth_, **kwargs):
        super(FacebookRemoteApp, self).__init__(
            oauth_, models.FACEBOOK, **kwargs)

    def exchange_token(self, token):
        """Authorizes user by exchanging short-lived token for long-lived."""

        url = self.expand_url(self.access_token_url)
        data = dict(client_id=self.consumer_key,  # XXX: Add appsecret_proof
                    client_secret=self.consumer_secret, fb_exchange_token=token,
                    grant_type='fb_exchange_token')
        url = oauth_common.add_params_to_uri(url, data)
        resp, content = self.http_request(url)
        data = f_oauth_client.parse_response(resp, content, self.content_type)
        if resp.code not in (200, 201):
            try:
                message = data['error']['message']
            except (KeyError, TypeError):
                message = 'Failed to exchange token for {}'.format(self.name)
            raise f_oauth_client.OAuthException(
                message, type='token_exchange_failed', data=data)
        return data


facebook = FacebookRemoteApp(
    oauth,
    base_url='https://graph.facebook.com',
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    app_key='FACEBOOK'
)
if models.FACEBOOK not in oauth.remote_apps:
    oauth.remote_apps[models.FACEBOOK] = facebook


@facebook.tokengetter
def facebook_tokengetter():
    """Returns Facebook access token object. Used for authenticated requests."""
    # Note: remote app doesn't support tokensetter
    if flask.request.user:
        token = models.Token.query.filter(
            user_id=flask.user.id, service=models.FACEBOOK).first()
        return token.access_token, ''
    return None


class Client(object):
    """Eucaby client for mobile app.

    Note: Client is not needed for password grant authentication but
    oautlib still uses client in the code (bug?)
    """
    client_id = models.EUCABY

    @property
    def client_type(self):
        return 'public'

    @property
    def default_scopes(self):
        return ['profile', 'history', 'location']


PARAM_MISSING = 'Missing {param} parameter'


def code2error(code, description=''):
    def _missing(param_, code_, message_, field_message_):
        return dict(
            message=message_, code=code_, fields={param_: field_message_}), 400

    if code == 'unsupported_grant_type':
        return _missing(
            'grant_type', code, 'Grant type is not supported',
            'Grant type is missing or invalid')
    elif code == 'invalid_request':
        params = ('service', 'password', 'username', 'grant_type', 'scope',
                  'refresh_token')
        for param in params:
            # Hack to match invalid_request description with the fields
            key = param.replace('_', ' ')
            if key in description:
                return _missing(
                    param, code, description, PARAM_MISSING.format(param=param))
    return None


def format_auth_response(resp):
    """Formats auth errors."""
    if resp.status_code == 200:
        return resp
    data = json.loads(resp.data)
    message = ''
    if 'error_description' in data:
        message = data['error_description']
    error_code = data['error']
    resp = code2error(error_code, message)
    if resp is not None:
        return api_utils.make_error(*resp)
    error = dict(message=message, code=error_code)
    return api_utils.make_error(error, 403)


def eucaby_clientgetter(client_id):  # pylint: disable=unused-argument
    """Simple client getter."""
    return Client()


def eucaby_tokengetter(access_token=None, refresh_token=None):
    """Returns token object based on access_token or refresh_token."""
    # Either access_token or refresh_token can be set at a time
    if access_token:
        return models.Token.query.filter_by(
            access_token=access_token, service=models.EUCABY).first()
    elif refresh_token:
        return models.Token.query.filter_by(
            refresh_token=refresh_token, service=models.EUCABY).first()
    return None


def eucaby_tokensetter(token, request, *args, **kwargs):  # pylint: disable=unused-argument
    """Creates both Eucaby and Facebook tokens."""
    user = request.user
    fb_token = request.facebook_token
    ec_token = request.eucaby_token
    if request.grant_type == GRANT_TYPE_PASSWORD and fb_token:
        models.Token.create_facebook_token(
            user.id, fb_token['access_token'], int(fb_token['expires']))
        return models.Token.create_eucaby_token(user.id, token)
    elif request.grant_type == GRANT_TYPE_REFRESH and ec_token:
        return ec_token.update_token(token)
    raise oauth_oauth2.InvalidRequestError('Failed to set token')


class EucabyValidator(provider.OAuth2RequestValidator):

    def __init__(self, clientgetter, tokengetter, tokensetter):
        self._clientgetter = clientgetter
        self._tokengetter = tokengetter
        self._tokensetter = tokensetter

    def client_authentication_required(self, request):
        return False

    def authenticate_client_id(self, client_id, request):
        return self.validate_client_id(client_id, request)

    def validate_user(self, username, password, client, request):
        """Ensures that user exists for valid username and password.

        username:   Facebook user id
        password:   Facebook short lived token

        Note:
            Username and password are passed in Eucaby authentication request
            This method is not executed for refresh token request
        """
        # Exchange short lived token for the long lived token
        try:
            # Exchange short lived token for the long lived token
            # Returns dictionary with access token
            fb_token = facebook.exchange_token(password)
        except f_oauth_client.OAuthException as ex:
            raise oauth_oauth2.InvalidGrantError(ex.message)
        access_token = fb_token['access_token']
        user = models.User.query.filter_by(username=username).first()
        if user is None:
            try:
                # Facebook profile request
                resp_me = facebook.get('/me', token=(access_token, ''))
            except f_oauth_client.OAuthException as ex:
                raise oauth_oauth2.InvalidGrantError(ex.message)

            resp_data = resp_me.data.copy()
            username = str(resp_data.pop('id'))
            resp_data['username'] = username  # Set user id from Facebook
            # Create user profile from Facebook data
            user = models.User.create(**resp_data)

        # Username should match Facebook user id
        if username != request.body['username']:
            raise oauth_oauth2.InvalidGrantError('Invalid username')

        request.user = user
        request.facebook_token = fb_token  # Set facebook_token attribute
        return user


    def validate_refresh_token(self, refresh_token, client, request):
        """Validates Eucaby refresh token."""
        token = self._tokengetter(refresh_token=refresh_token)
        if token:
            request.eucaby_token = token
            request.user = token.user
            return True
        raise oauth_oauth2.InvalidGrantError('Invalid refresh token')

    def validate_grant_type(self, client_id, grant_type, client, request):
        return grant_type in GRANT_TYPE_CHOICES

    def save_bearer_token(self, token, request, *args, **kwargs):
        self._tokensetter(token, request, *args, **kwargs)


class EucabyOAuth2Provider(provider.OAuth2Provider):

    def validate_extra_params(self):
        """Validates extra params."""
        form = flask.request.form
        param = 'service'
        if (form.get('grant_type') == GRANT_TYPE_PASSWORD and
                form.get(param) != models.FACEBOOK):
            raise oauth_oauth2.InvalidRequestError(
                PARAM_MISSING.format(param=param))

    def token_handler(self, f):
        """Access or refresh token handler decorator."""
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            try:
                self.validate_extra_params()
            except oauth_oauth2.OAuth2Error as e:
                resp = flask.make_response(e.json, e.status_code)
                return format_auth_response(resp)
            resp = (super(EucabyOAuth2Provider, self)
                    .token_handler(f)(*args, **kwargs))
            return format_auth_response(resp)
        return decorated

eucaby_oauth = EucabyOAuth2Provider()
eucaby_oauth._validator = EucabyValidator(  # pylint: disable=attribute-defined-outside-init,protected-access
    eucaby_clientgetter, eucaby_tokengetter, eucaby_tokensetter)
