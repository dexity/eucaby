"""Views for Eucaby API."""

import flask
import flask_restful

from eucaby_api import auth
from eucaby_api.utils import api as restful_api


api_app = flask.Blueprint('api', __name__)
api = restful_api.Api(api_app)


class OAuthToken(flask_restful.Resource):

    method_decorators = [auth.eucaby_oauth.token_handler]

    def post(self):
        return None


class FriendsView(flask_restful.Resource):

    """Returns list of friends."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):
        return dict(hello='world')


api.add_resource(OAuthToken, '/oauth/token')
api.add_resource(FriendsView, '/friends')
