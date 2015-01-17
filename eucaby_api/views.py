"""Views for Eucaby API."""

import flask
import flask_restful

from eucaby_api import auth
from eucaby_api import fields as api_fields
from eucaby_api.utils import api as eucaby_api
from eucaby_api.utils import utils as api_utils


api_app = flask.Blueprint('api', __name__)
api = eucaby_api.Api(api_app)


class OAuthToken(flask_restful.Resource):

    method_decorators = [auth.eucaby_oauth.token_handler]

    def post(self):  # pylint: disable=no-self-use
        return None


class FriendsView(flask_restful.Resource):

    """Returns list of friends."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        user = flask.request.user
        resp = auth.facebook.get('/{}/friends'.format(user.username))
        return api_utils.format_fb_response(resp, api_fields.FRIENDS_FIELDS)


api.add_resource(OAuthToken, '/oauth/token')
api.add_resource(FriendsView, '/friends')
