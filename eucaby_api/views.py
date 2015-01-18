"""Views for Eucaby API."""

import flask
import flask_restful

from eucaby_api import auth
from eucaby_api import fields as api_fields
from eucaby_api.utils import api as eucaby_api
from eucaby_api.utils import utils as api_utils


api_app = flask.Blueprint('api', __name__)
api = eucaby_api.Api(api_app, catch_all_404s=True)


class OAuthToken(flask_restful.Resource):

    method_decorators = [auth.eucaby_oauth.token_handler]

    def post(self):  # pylint: disable=no-self-use
        return None


class FriendsView(flask_restful.Resource):

    """Returns list of friends."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        user = flask.request.user
        resp = auth.facebook_request(
            'get', '/{}/friends'.format(user.username))
        return api_utils.format_fb_response(resp, api_fields.FRIENDS_FIELDS)


class RequestLocationView(flask_restful.Resource):

    """Performs user's location request."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    def post(self):  # pylint: disable=no-self-use
        # XXX: Implement
        return


class NotifyLocationView(flask_restful.Resource):

    """Notifies user's location."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    def post(self):  # pylint: disable=no-self-use
        # XXX: Implement
        return


class UserActivityView(flask_restful.Resource):

    """Returns list of user activity."""
    method_decorators = [auth.eucaby_oauth.require_oauth('history')]

    def get(self):  # pylint: disable=no-self-use
        # XXX: Implement
        return



class UserProfileView(flask_restful.Resource):

    """Returns user profile details."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        # XXX: Implement
        return



api.add_resource(OAuthToken, '/oauth/token')
api.add_resource(FriendsView, '/friends')
api.add_resource(RequestLocationView, '/location/request')
api.add_resource(NotifyLocationView, '/location/notify')
api.add_resource(UserProfileView, '/me')
api.add_resource(UserActivityView, '/history')
