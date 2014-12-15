"""Views for Eucaby API."""
# from eucaby_api.wsgi import app

import flask
from flask.ext import restful
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils

from eucaby_api import auth

api_app = flask.Blueprint('api', __name__)
api = restful.Api(api_app)

# Messages
PARAM_MISSING = 'Missing required parameter {param}'
INVALID_SERVICE = 'Invalid service'
GRANT_TYPES = 'Valid grant types are password and refresh_token'
GRANT_TYPE_PASSWORD = 'password'
GRANT_TYPE_REFRESH = 'refresh_token'
# Choices
GRANT_TYPE_CHOICES = [GRANT_TYPE_PASSWORD, GRANT_TYPE_REFRESH]


class OAuthToken(restful.Resource):

    #@classmethod
    #def handle_password_grant(cls):


    def post(self):
        """Authentication handler."""
        args = None
        # Password grant type
        parser = reqparse.RequestParser()
        params = ['username', 'password']
        for param in params:
            parser.add_argument(param, type=str, required=True,
                                help=PARAM_MISSING.format(param=param))
        service_arg = reqparse.Argument(
            'service', type=str, required=True,
            choices=['facebook', ], help=INVALID_SERVICE)
        grant_type_arg = reqparse.Argument(
            name='grant_type', type=str, required=True,
            choices=GRANT_TYPE_CHOICES, help=GRANT_TYPES)
        parser.add_argument(service_arg)
        parser.add_argument(grant_type_arg)
        try:
            args = parser.parse_args()
            # Exchange short lived token for the long lived token
            service = args['service']
            grant_type = args['grant_type']
            sl_token = args['password']
            fb_user_id = args['username']

            resp = auth.facebook.exchange_token(sl_token)
            # if isinstance(resp, auth.f_oauth_client.OAuthException):
            #     return 'Access denied: %s' % resp.message

            # XXX: Finish
            # Returns either Eucaby access token or error
            # Lookup sl_token and make request to FB:
            #   - If exists and sl_token is valid update access token.
            #   - If exists and sl_token is not valid return "expired" error
            #   - If doesn't exist sl_token is valid create a new record
            #   - If doesn't exist sl_token is not valid return "invalid" error
            # Note: Token exchange can create Eucaby access token but it can't refresh it
        except reqparse.InvalidError as e:
            if not ('grant_type' in e.namespace
                and e.namespace['grant_type'] == GRANT_TYPE_PASSWORD):
                error = dict(message='Invalid request parameters', code='invalid',
                             fields=e.errors)

                print e.errors, e.namespace
                return api_utils.make_error(error, 400)



        # Refresh token grant type
        if not args:
            parser = reqparse.RequestParser()


        # Exchange and save token
        # ll_access_token = auth.fb_exchange_token()


        # resp['access_token']
        # Create (if it doesn't exist) or update user

        return {'hello': 'world'}

api.add_resource(OAuthToken, '/oauth/token')

