import flask
from flask_oauthlib import client as oauthlib_client
from oauthlib.oauth2.rfc6749 import parameters

oauth = oauthlib_client.OAuth()

class FacebookRemoteApp(oauthlib_client.OAuthRemoteApp):

    def __init__(self, oauth_, **kwargs):
        super(FacebookRemoteApp, self).__init__(oauth_, 'facebook', **kwargs)

    def exchange_token(self, token):
        """Authorizes user by exchanging short-lived token for long-lived."""
        client = self.make_client()

        params = dict(
            grant_type='fb_exchange_token', fb_exchange_token=token, client_secret=self.consumer_secret)
            # client_id=self.consumer_key,
            # client_secret=self.consumer_secret, fb_exchange_token=token)
        url = # parameters.prepare_grant_uri( #client.prepare_refresh_token_request( #prepare_token_request(  # prepare_request_uri(
            self.expand_url(self.access_token_url),
            **params
        )
        print url


facebook = FacebookRemoteApp(
    oauth,
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    app_key='FACEBOOK'
)
if 'facebook' not in oauth.remote_apps:
    oauth.remote_apps['facebook'] = facebook

def fb_exchange_token():
    resp = facebook.exchange_token('hello')
    # print resp.data
