"""Authentication module."""

import flask
from flask_oauthlib import client as f_oauth_client
from oauthlib import common as oauth_common

from eucaby_api import models

oauth = f_oauth_client.OAuth()


class FacebookRemoteApp(f_oauth_client.OAuthRemoteApp):

    """Facebook remote app."""

    def __init__(self, oauth_, **kwargs):
        super(FacebookRemoteApp, self).__init__(oauth_, 'facebook', **kwargs)

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
if 'facebook' not in oauth.remote_apps:
    oauth.remote_apps['facebook'] = facebook


@facebook.tokengetter
def get_facebook_access_token():
    """Returns Facebook access token."""
    # XXX: Add logged_in decorator
    # Order by expires_date?
    token = models.Token.query.filter(
        user_id=flask.session['user_id'], service=models.FACEBOOK).first()

    access_token = token and token.access_token or ''
    return access_token, ''
