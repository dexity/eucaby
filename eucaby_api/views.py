"""Views for Eucaby API."""

import flask
import flask_restful
from eucaby_api import auth
from eucaby_api import models
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils


api_app = flask.Blueprint('api', __name__)
api = flask_restful.Api(api_app)

# Messages
PARAM_MISSING = 'Missing required parameter {param}'
INVALID_SERVICE = 'Invalid service'
GRANT_TYPES = 'Valid grant types are password and refresh_token'
GRANT_TYPE_PASSWORD = 'password'
GRANT_TYPE_REFRESH = 'refresh_token'

# Choices
GRANT_TYPE_CHOICES = [GRANT_TYPE_PASSWORD, GRANT_TYPE_REFRESH]


class OAuthToken(flask_restful.Resource):
    """Handles oauth requests."""

    @classmethod
    def parse_grant_type(cls):
        """Parses grant_type argument or throws exception."""
        parser = reqparse.RequestParser()
        grant_type_arg = reqparse.Argument(
            name='grant_type', type=str, required=True,
            choices=GRANT_TYPE_CHOICES, help=GRANT_TYPES)
        parser.add_argument(grant_type_arg)
        args = parser.parse_args()
        return args['grant_type']

    @classmethod
    def password_grant_parser(cls):
        """Returns password grant parser."""
        parser = reqparse.RequestParser()
        params = ['username', 'password']
        for param in params:
            parser.add_argument(param, type=str, required=True,
                                help=PARAM_MISSING.format(param=param))
        service_arg = reqparse.Argument(
            'service', type=str, required=True,
            choices=[models.FACEBOOK, ], help=INVALID_SERVICE)
        grant_type_arg = reqparse.Argument(
            name='grant_type', type=str, required=True,
            choices=[GRANT_TYPE_PASSWORD, ], help=GRANT_TYPES)
        parser.add_argument(service_arg)
        parser.add_argument(grant_type_arg)
        return parser

    @classmethod
    def refresh_grant_parser(cls):
        """Returns refresh grant parser."""
        parser = reqparse.RequestParser()
        grant_type_arg = reqparse.Argument(
            name='grant_type', type=str, required=True,
            choices=[GRANT_TYPE_REFRESH, ], help=GRANT_TYPES)
        refresh_arg = reqparse.Argument(
            name='refresh_token', type=str, required=True,
            help=PARAM_MISSING.format(param='refresh_token'))
        parser.add_argument(grant_type_arg)
        parser.add_argument(refresh_arg)
        return parser

    def handle_password_grant(self):
        """Handles password grant_type."""
        parser = self.password_grant_parser()
        try:
            args = parser.parse_args(strict=True)
        except reqparse.InvalidError as ex:
            errors = ex.errors
            errors.update(ex.unparsed)
            error = dict(message='Invalid request parameters',
                         code='invalid', fields=errors)
            return api_utils.make_error(error, 400)

        assert args['service'], models.FACEBOOK
        assert args['grant_type'], GRANT_TYPE_PASSWORD
        fb_short_token = args['password']
        fb_user_id = args['username']

        try:
            # Exchange short lived token for the long lived token
            resp_token = auth.facebook.exchange_token(fb_short_token)
        except auth.f_oauth_client.OAuthException as ex:
            error = dict(message=ex.message, code='invalid_oauth')
            return api_utils.make_error(error, 403)

        access_token = resp_token['access_token']
        user = models.User.query.filter_by(username=fb_user_id).first()
        if user is None:
            try:
                # Facebook profile request
                resp_me = auth.facebook.get('/me', token=(access_token, ''))
            except auth.f_oauth_client.OAuthException as ex:
                error = dict(message=ex.message, code='invalid_oauth')
                return api_utils.make_error(error, 401)

            username = str(resp_me.pop('id'))
            resp_me['username'] = username
            # Create user profile from Facebook data
            user = models.User.create(**resp_me)

        # Username should match Facebook user id
        if user.username != fb_user_id:
            error = dict(message='Invalid username', code='invalid_user')
            return api_utils.make_error(error, 400)

        # Create Facebook and Eucaby tokens
        models.Token.create_facebook_token(
            user.id, access_token, resp_token['expires'])
        ec_token = models.Token.create_eucaby_token(user.id)
        flask.session['user_id'] = user.id
        return ec_token.to_response()

    def handle_refresh_grant(self):
        """Handles refresh token grant type."""
        parser = self.refresh_grant_parser()
        try:
            args = parser.parse_args(strict=True)
        except reqparse.InvalidError as ex:
            errors = ex.errors
            errors.update(ex.unparsed)
            error = dict(message='Invalid request parameters',
                         code='invalid', fields=errors)
            return api_utils.make_error(error, 400)

        token = models.Token.update_token(args['refresh_token'])
        if token is None:
            error = dict(message='Invalid refresh token', code='invalid_token')
            return api_utils.make_error(error, 404)
        return token.to_response()

    def post(self):
        """Authentication handler."""
        try:
            grant_type = self.parse_grant_type()
        except reqparse.InvalidError as ex:
            error = dict(message='Invalid request parameters',
                         code='invalid_grant', fields=ex.errors)
            return api_utils.make_error(error, 400)

        if grant_type == GRANT_TYPE_PASSWORD:
            return self.handle_password_grant()

        return self.handle_refresh_grant()


api.add_resource(OAuthToken, '/oauth/token')
