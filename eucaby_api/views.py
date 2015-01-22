"""Views for Eucaby API."""

import flask
from flask import current_app
import flask_restful
import logging

from eucaby.utils import mail as utils_mail
from eucaby_api import auth
from eucaby_api import fields as api_fields
from eucaby_api.utils import api as eucaby_api
from eucaby_api import args as api_args
from eucaby_api import models
from eucaby_api import ndb_models
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils


api_app = flask.Blueprint('api', __name__)
api = eucaby_api.Api(api_app, catch_all_404s=True)


USER_NOT_FOUND = 'User not found'


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
        args = reqparse.clean_args(api_args.REQUEST_LOCATION_ARGS)
        if isinstance(args, flask.Response):
            return args
        username, email = args['username'], args['email']
        if not (username or email):
            error = dict(message=api_args.MISSING_EMAIL_USERNAME,
                         code='invalid_request')
            return api_utils.make_response(error, 400)
        user = flask.request.user  # Sender

        recipient_username, recipient_name, recipient_email = None, None, None
        # Either recipient username or email will be set, not both
        if email:  # Email has priority over username
            recipient_email = email
        elif username:
            recipient = models.User.query.filter_by(username=username).first()
            if not recipient or (recipient and not recipient.is_active):
                error = dict(message=USER_NOT_FOUND, code='not_found')
                return api_utils.make_response(error, 404)
            recipient_name = recipient.name
            recipient_username = recipient.username
            recipient_email = recipient.email

        noreply_email = current_app.config['NOREPLY_EMAIL']
        session = ndb_models.Session.create(
            user.username, recipient_username, recipient_email)
        req = ndb_models.LocationRequest.create(session)

        # XXX: Add user configuration to receive notifications to email
        #      (for Eucaby users). See #18
        if recipient_email:
            # Send email notification
            # XXX: Make host url configurable
            body = flask.render_template(
                'mail/location_request_body.txt', sender_name=user.name,
                recipient_name=recipient_name,
                url='http://eucaby-dev.appspot.com/{}'.format(req.token))
            utils_mail.send_mail(
                'Location Request', body, noreply_email, [recipient_email])
        logging.info('Location Request: %s', str(req.to_dict()))

        return flask_restful.marshal(
            req, api_fields.REQUEST_LOCATION_FIELDS, envelope='data')


class NotifyLocationView(flask_restful.Resource):

    """Notifies user's location."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    def post(self):  # pylint: disable=no-self-use
        # XXX: Implement
        # session = core_models.Session.create(
        #     request.sender_email, request.receiver_email)
        # resp = core_models.Response.create(session, request.latlng)
        # kwargs = resp.to_dict()
        # logging.info(kwargs)
        # return api_messages.Response(**kwargs)
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
