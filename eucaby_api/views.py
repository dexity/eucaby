"""Views for Eucaby API."""

import flask
from flask import current_app
import flask_restful
import itertools
import json
import logging

from google.appengine.api import memcache

from eucaby_api import auth
from eucaby_api import fields as api_fields
from eucaby_api.utils import api as eucaby_api
from eucaby_api.utils import gae as gae_utils
from eucaby_api import args as api_args
from eucaby_api import models
from eucaby_api import ndb_models
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils

api_app = flask.Blueprint('api', __name__)
api = eucaby_api.Api(api_app, catch_all_404s=True)


USER_NOT_FOUND = 'User not found'
MAP_BASE = 'https://maps.google.com/maps'


class IndexView(flask_restful.Resource):

    """Index view."""
    def get(self):  # pylint: disable=no-self-use
        data = dict(message='Yo, dude. I am here :).')
        return flask_restful.marshal(
            data, api_fields.INDEX_FIELDS, envelope='data')


class OAuthToken(flask_restful.Resource):

    method_decorators = [auth.eucaby_oauth.token_handler]

    def post(self):  # pylint: disable=no-self-use
        return None


class FriendsView(flask_restful.Resource):

    """Returns list of friends."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        user = flask.request.user
        cache_key = api_utils.create_key('user_id', user.id, 'friends')
        cached_data = memcache.get(cache_key)
        # Note: If request has get parameter 'refresh=1' then do not use cache
        if cached_data and flask.request.args.get('refresh') != '1':
            resp = flask.make_response(cached_data)
            resp.mimetype = 'application/json'
            return resp
        resp = auth.facebook_request(
            'get', '/{}/friends'.format(user.username))
        fresp = api_utils.format_fb_response(resp, api_fields.FRIENDS_FIELDS)
        if resp.status not in api_utils.SUCCESS_STATUSES:
            return fresp
        # Sort friends by name
        data = dict(data=sorted(fresp['data'], key=lambda x: x['name']))
        memcache.set(cache_key, json.dumps(data), api_args.DAY)
        return data


class RequestLocationView(flask_restful.Resource):

    """Performs user's location request."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    @classmethod
    def _handle_request(cls, recipient, recipient_email):
        """Handles general operations of the request."""
        recipient_username = (recipient and recipient.username) or None
        recipient_name = (recipient and recipient.name) or None
        message = flask.request.message
        user = flask.request.user  # Sender
        req = ndb_models.LocationRequest.create(
            user.username, user.name, recipient_username=recipient_username,
            recipient_name=recipient_name, recipient_email=recipient_email,
            message=message)

        # Send notifications to Android and iOS devices of the registered user
        # (sender and recipient can be the same person)
        if recipient_username:
            gae_utils.send_notification(
                recipient_username, user.name, api_args.REQUEST, req.id)

        if recipient_email:
            # Do not send email if email_subscription is False
            if recipient and not models.UserSettings.user_param(
                    recipient.id, api_args.EMAIL_SUBSCRIPTION):
                pass
            else:
                # Send email notification to recipient
                eucaby_url = current_app.config['EUCABY_URL']
                req_url = '{}/request/{}'.format(eucaby_url, req.uuid)
                body = flask.render_template(
                    'mail/location_request_body.txt', sender_name=user.name,
                    recipient_name=recipient_name, eucaby_url=eucaby_url,
                    url=req_url, message=message)
                gae_utils.send_mail('New Request', body, [recipient_email])
        logging.info('New Request: uuid=%s', req.uuid)
        return flask_restful.marshal(
            req.to_dict(), api_fields.REQUEST_FIELDS, envelope='data')

    @classmethod
    def handle_email(cls, email):
        """Handles email parameter."""
        recipient = models.User.get_by_email(email)
        user = flask.request.user
        models.EmailHistory.get_or_create(user.id, email)
        return cls._handle_request(recipient, email)

    @classmethod
    def handle_username(cls, username):
        """Handles username parameter."""
        recipient = models.User.get_by_username(username)
        if not recipient:
            error = dict(message=USER_NOT_FOUND, code='not_found')
            return api_utils.make_response(error, 404)
        # Note:
        #     Recipient email can be empty because Facebook doesn't guarantee it
        # See:
        #     https://developers.facebook.com/docs/graph-api/reference/v2.2/user
        #     "This field will not be returned if no valid email address is
        #     available."
        return cls._handle_request(recipient, recipient.email)

    def post(self):
        args = reqparse.clean_args(api_args.REQUEST_LOCATION_ARGS)
        if isinstance(args, flask.Response):
            return args

        username, email = args['username'], args['email']
        flask.request.message = args['message']
        # Email has priority over username
        if email:
            return self.handle_email(email)
        elif username:
            return self.handle_username(username)

        error = dict(
            message=api_args.MISSING_EMAIL_USERNAME, code='invalid_request')
        return api_utils.make_response(error, 400)


class NotifyLocationView(flask_restful.Resource):

    """Notifies user's location."""
    method_decorators = [auth.eucaby_oauth.require_oauth('location')]

    @classmethod
    def _handle_request(cls, recipient, recipient_email, latlng, session=None):
        """Handles general operations of the request."""
        recipient_username = (recipient and recipient.username) or None
        recipient_name = (recipient and recipient.name) or None
        message = flask.request.message
        user = flask.request.user  # Sender
        # Create location response
        # Notes:
        #   - There might be several location responses for a single session
        #   - API requests are considered as mobile
        loc_notif = ndb_models.LocationNotification.create(
            latlng, user.username, user.name,
            recipient_username=recipient_username,
            recipient_name=recipient_name, recipient_email=recipient_email,
            message=message, session=session)

        # Send notifications to Android and iOS devices of the registered user
        # (sender and recipient can be the same person)
        if recipient_username:
            gae_utils.send_notification(
                recipient_username, user.name, api_args.NOTIFICATION,
                loc_notif.id)

        if recipient_email:
            # Do not send email if email_subscription is False
            if recipient and not models.UserSettings.user_param(
                    recipient.id, api_args.EMAIL_SUBSCRIPTION):
                pass
            else:
                # Send email notification to recipient
                eucaby_url = current_app.config['EUCABY_URL']
                location_url = '{}/location/{}'.format(
                    eucaby_url, loc_notif.uuid)
                body = flask.render_template(
                    'mail/location_response_body.txt', sender_name=user.name,
                    recipient_name=recipient_name, eucaby_url=eucaby_url,
                    location_url=location_url, message=message)
                gae_utils.send_mail(
                    'New Location', body, [recipient_email])
        logging.info('New Location: uuid=%s', loc_notif.uuid)
        return flask_restful.marshal(
            loc_notif.to_dict(), api_fields.NOTIFICATION_FIELDS,
            envelope='data')

    @classmethod
    def handle_token(cls, token, latlng):
        """Handles token parameter."""
        # Get location request
        loc_req = ndb_models.LocationRequest.get_by_session_token(token)
        if not loc_req:
            error = dict(message='Request not found', code='not_found')
            return api_utils.make_response(error, 404)
        # XXX: Only sender or receiver can notify location
        loc_req = loc_req[0]
        session = loc_req.session
        # Get recipient which is sender in the session
        recipient = models.User.get_by_username(loc_req.sender_username)
        if not recipient:
            error = dict(message=USER_NOT_FOUND, code='not_found')
            return api_utils.make_response(error, 404)
        session.complete = True
        loc_req.session = session
        loc_req.put()
        return cls._handle_request(recipient, recipient.email, latlng, session)

    @classmethod
    def handle_email(cls, email, latlng):
        """Handles email parameter."""
        recipient = models.User.get_by_email(email)
        user = flask.request.user
        models.EmailHistory.get_or_create(user.id, email)
        return cls._handle_request(recipient, email, latlng)

    @classmethod
    def handle_username(cls, username, latlng):
        """Handles username parameter."""
        recipient = models.User.get_by_username(username)
        if not recipient:
            error = dict(message=USER_NOT_FOUND, code='not_found')
            return api_utils.make_response(error, 404)
        return cls._handle_request(recipient, recipient.email, latlng)

    def post(self):
        args = reqparse.clean_args(api_args.NOTIFY_LOCATION_ARGS)
        if isinstance(args, flask.Response):
            return args

        username, email, token, latlng = (
            args['username'], args['email'], args['token'], args['latlng'])
        flask.request.message = args['message']
        # Preference chain: token, email, username
        if token:
            return self.handle_token(token, latlng)
        elif email:
            return self.handle_email(email, latlng)
        elif username:
            return self.handle_username(username, latlng)

        error = dict(message=api_args.MISSING_EMAIL_USERNAME_REQ,
                     code='invalid_request')
        return api_utils.make_response(error, 400)


class UserProfileView(flask_restful.Resource):

    """Returns user profile details."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        user = flask.request.user
        return flask_restful.marshal(
            user.to_dict(), api_fields.USER_FIELDS, envelope='data')


class UserSettingsView(flask_restful.Resource):

    """Returns or updates user settings."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def get(self):  # pylint: disable=no-self-use
        """Get user settings."""
        user = flask.request.user
        obj = models.UserSettings.get_or_create(user.id)
        return flask_restful.marshal(
            obj.to_dict(), api_fields.SETTINGS_FIELDS, envelope='data')

    def post(self):  # pylint: disable=no-self-use
        """Update user settings."""
        args = reqparse.clean_args(api_args.SETTINGS_ARGS, strict=True)
        if isinstance(args, flask.Response):
            return args
        user = flask.request.user
        obj = models.UserSettings.get_or_create(user.id)
        obj.update(
            {api_args.EMAIL_SUBSCRIPTION: args[api_args.EMAIL_SUBSCRIPTION]})
        return flask_restful.marshal(
            obj.to_dict(), api_fields.SETTINGS_FIELDS, envelope='data')


class UserActivityView(flask_restful.Resource):

    """Returns list of user activity."""
    method_decorators = [auth.eucaby_oauth.require_oauth('history')]

    @classmethod
    def _get_vector_data(cls, requests, notifications, offset, limit):
        """Returns data dictionary with merged requests and notifications."""
        data = []
        items = itertools.chain(requests, notifications)
        merged_items = sorted(
            items, key=lambda x: x.created_date, reverse=True)
        # Alternative solution:
        # merged_items = api_utils.merge_sorted_queries(
        #     [requests, notifications], offset + limit,
        #     key=lambda x: x.created_date, reverse=True)
        for item in merged_items[offset:offset+limit]:
            if isinstance(item, ndb_models.LocationRequest):
                data_item = flask_restful.marshal(
                    item.to_dict(), api_fields.REQUEST_FIELDS)
            else:
                data_item = flask_restful.marshal(
                    item.to_dict(), api_fields.NOTIFICATION_FIELDS)
            data.append(data_item)
        return dict(data=data)

    @classmethod
    def get_outgoing_data(cls, offset, limit):
        """Returns data for outgoing activities."""
        username = flask.request.user.username
        size = offset + limit
        requests = ndb_models.LocationRequest.get_by_sender_username(
            username, offset=0, limit=size)
        notifications = (ndb_models.LocationNotification
                         .get_by_sender_username(username, offset=0,
                                                 limit=size))
        return cls._get_vector_data(requests, notifications, offset, limit)

    @classmethod
    def get_incoming_data(cls, offset, limit):
        """Returns data for request activities."""
        username = flask.request.user.username
        size = offset + limit
        requests = (ndb_models.LocationRequest
                    .get_by_recipient_username(username, offset=0, limit=size))
        notifications = (ndb_models.LocationNotification
                         .get_by_recipient_username(username, offset=0,
                                                    limit=size))
        return cls._get_vector_data(requests, notifications, offset, limit)

    @classmethod
    def get_request_data(cls, offset, limit):
        """Returns data for request activities."""
        username = flask.request.user.username
        requests = ndb_models.LocationRequest.get_by_sender_username(
            username, offset=offset, limit=limit)
        return flask_restful.marshal(
            dict(data=[req.to_dict() for req in requests]),
            api_fields.REQUEST_LIST_FIELDS)

    @classmethod
    def get_notification_data(cls, offset, limit):
        """Returns data for notification activities."""
        username = flask.request.user.username
        notifications = ndb_models.LocationNotification.get_by_sender_username(
            username, offset=offset, limit=limit)

        return flask_restful.marshal(
            dict(data=[notif.to_dict() for notif in notifications]),
            api_fields.NOTIFICATION_LIST_FIELDS)

    @classmethod
    def _handle_request(cls, act_type, offset, limit):
        """Handles request."""
        # Note: total number of requests and notifications is not very important
        if act_type == api_args.OUTGOING:
            resp = cls.get_outgoing_data(offset, limit)
        elif act_type == api_args.INCOMING:
            resp = cls.get_incoming_data(offset, limit)
        elif act_type == api_args.REQUEST:
            resp = cls.get_request_data(offset, limit)
        elif act_type == api_args.NOTIFICATION:
            resp = cls.get_notification_data(offset, limit)
        # Add pagination
        if resp:
            resp['paging'] = dict(next_offset=offset+limit, limit=limit)
            return resp

        error = dict(message=api_args.DEFAULT_ERROR, code='server_error')
        return api_utils.make_response(error, 500)

    def get(self):
        args = reqparse.clean_args(api_args.ACTIVITY_ARGS)
        if isinstance(args, flask.Response):
            return args
        limit = args['limit']
        if limit > 100:  # Limit can't exceed 100
            limit = 100
        return self._handle_request(args['type'], args['offset'], limit)


class RequestDetailView(flask_restful.Resource):

    """Returns request detail view."""
    method_decorators = [auth.eucaby_oauth.require_oauth('history')]

    def get(self, req_id):  # pylint: disable=no-self-use
        loc_req = ndb_models.LocationRequest.get_by_id(req_id)
        if not loc_req:
            error = dict(message='Location request not found', code='not_found')
            return api_utils.make_response(error, 404)

        # If user is sender or recipient return authorization error
        user = flask.request.user
        username = user.username
        if not (loc_req.sender_username == username or
                loc_req.recipient_username == username):
            error = dict(
                message='Not authorized to access the data', code='auth_error')
            return api_utils.make_response(error, 401)
        # Look up related notifications
        notifications = ndb_models.LocationNotification.get_by_session_token(
            loc_req.session.token)
        resp_dict = loc_req.to_dict()
        resp_dict['notifications'] = [
            notif.to_dict() for notif in notifications]

        return flask_restful.marshal(
            resp_dict, api_fields.DETAIL_REQUEST_FIELDS, envelope='data')


class NotificationDetailView(flask_restful.Resource):

    """Returns notification detail view."""
    method_decorators = [auth.eucaby_oauth.require_oauth('history')]

    def get(self, notif_id):  # pylint: disable=no-self-use
        loc_notif = ndb_models.LocationNotification.get_by_id(notif_id)
        if not loc_notif:
            error = dict(
                message='Location notification not found', code='not_found')
            return api_utils.make_response(error, 404)

        # If user is sender or recipient return authorization error
        user = flask.request.user
        username = user.username
        if not (loc_notif.sender_username == username or
                loc_notif.recipient_username == username):
            error = dict(
                message='Not authorized to access the data', code='auth_error')
            return api_utils.make_response(error, 401)
        # Look up related notifications
        request = ndb_models.LocationRequest.get_by_session_token(
            loc_notif.session.token)
        resp_dict = loc_notif.to_dict()
        resp_dict['request'] = (request and request[0]) or None

        return flask_restful.marshal(
            resp_dict, api_fields.DETAIL_NOTIFICATION_FIELDS, envelope='data')


class RegisterDeviceView(flask_restful.Resource):

    """Registers user device."""
    method_decorators = [auth.eucaby_oauth.require_oauth('profile')]

    def post(self):  # pylint: disable=no-self-use
        args = reqparse.clean_args(api_args.REGISTER_DEVICE_ARGS)
        if isinstance(args, flask.Response):
            return args

        user = flask.request.user
        obj = models.Device.get_or_create(
            user, args['device_key'], args['platform'])
        return flask_restful.marshal(obj, api_fields.DEVICE_FIELDS)


class AutocompleteView(flask_restful.Resource):

    """Returns notification detail view."""
    method_decorators = [auth.eucaby_oauth.require_oauth('history')]

    def get(self):  # pylint: disable=no-self-use
        args = reqparse.clean_args(api_args.AUTO_ARGS)
        if isinstance(args, flask.Response):
            return args

        user = flask.request.user
        emails = [obj.text for obj in models.EmailHistory.get_by_user(
            user.id, args['query'], args['limit'])]
        return flask_restful.marshal(
            dict(data=emails), api_fields.AUTO_FIELDS)


api.add_resource(IndexView, '/', endpoint='index')
api.add_resource(OAuthToken, '/oauth/token', endpoint='oauth_token')
api.add_resource(FriendsView, '/friends', endpoint='friends')
api.add_resource(RequestLocationView, '/location/request',
                 endpoint='request_location')
api.add_resource(RequestDetailView, '/location/request/<int:req_id>',
                 endpoint='request')
api.add_resource(NotifyLocationView, '/location/notification',
                 endpoint='notify_location')
api.add_resource(NotificationDetailView,
                 '/location/notification/<int:notif_id>',
                 endpoint='notification')
api.add_resource(UserProfileView, '/me', endpoint='profile')
api.add_resource(UserSettingsView, '/settings', endpoint='settings')
api.add_resource(UserActivityView, '/history', endpoint='history')
api.add_resource(RegisterDeviceView, '/device/register',
                 endpoint='register_device')
api.add_resource(AutocompleteView, '/autocomplete', endpoint='autocomplete')
