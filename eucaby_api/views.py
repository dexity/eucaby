"""Views for Eucaby API."""
# from eucaby_api.wsgi import app

import flask
from flask.ext import restful
from flask.ext.restful import reqparse

from eucaby_api import auth

api_app = flask.Blueprint('api', __name__)
api = restful.Api(api_app)

class OAuthToken(restful.Resource):
    def post(self):
        PARAM_REQ = 'Parameter {param} is required'
        parser = reqparse.RequestParser()
        params = ['service', 'grant_type', 'username', 'password']
        for param in params:
            parser.add_argument(
                param, type=str, required=True,
                help=PARAM_REQ.format(param=param))
        args = parser.parse_args()
        # Exchange short lived token for the long lived token
        service = args['service']  # Should be 'facebook'
        grant_type = args['grant_type']
        sl_token = args['password']
        fb_user_id = args['username']


        # Exchange and save token
        # ll_access_token = auth.fb_exchange_token()

        resp = auth.facebook.exchange_token(sl_token)
        # if isinstance(resp, auth.f_oauth_client.OAuthException):
        #     return 'Access denied: %s' % resp.message

        # session['oauth_token'] = (resp['access_token'], '')
        return {'hello': 'world'}


@api_app.route('/login/authorized')
def facebook_authorized():
    resp = auth.facebook.authorized_response()
    print 'facebook_authorized'
    print resp

api.add_resource(OAuthToken, '/oauth/token')

