
import apns
import flask
from flask import views
from flask import current_app
from gcm import gcm
import logging
from sqlalchemy import exc
import time

from eucaby_api import args as api_args
from eucaby_api import models
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils


tasks_app = flask.Blueprint('tasks', __name__)


class PushNotificationsTask(views.MethodView):

    methods = ['POST']

    @classmethod
    def handle_input(cls, platform):
        args = reqparse.clean_args(api_args.PUSH_TASK_ARGS, is_task=True)
        if isinstance(args, flask.Response):
            logging.error(str(args.data))
            return args

        flask.request.recipient_username = args['recipient_username']
        flask.request.sender_name = args['sender_name']
        flask.request.message_type = args['message_type']
        flask.request.message_id = args['message_id']

        devices = models.Device.get_by_username(
            flask.request.recipient_username, platform=platform)
        if not devices:
            msg = 'No android devices found'
            logging.info(msg)
            return flask.make_response(msg)
        flask.request.devices = devices


class GCMNotificationsTask(PushNotificationsTask):

    """Push notifications for GCM."""

    def post(self):  # pylint: disable=no-self-use
        res = self.handle_input(api_args.ANDROID)
        if isinstance(res, flask.Response):
            return res

        regs = {}
        for dev in flask.request.devices:
            regs[dev.device_key] = dev
        logging.info('Pushing GCM notifications to %s devices',
                     len(flask.request.devices))

        data = api_utils.payload_data(
            flask.request.sender_name, flask.request.message_type)
        gcm_app = gcm.GCM(current_app.config['GCM_API_KEY'])
        # Add message data
        data.update(dict(
            type=flask.request.message_type, id=flask.request.message_id))
        logging.info('GCM message payload: %s', str(data))
        try:
            resp = gcm_app.json_request(
                registration_ids=regs.keys(), data=data, retries=7)
        except gcm.GCMException as e:
            logging.error(
                'Failed to push notification. %s: %s',
                e.__class__.__name__, e.message)
            return e.message, 500

        msg = 'GCM result: {}'.format(str(resp))
        logging.info(msg)
        if 'errors' in resp:
            for error, reg_ids in resp['errors'].items():
                if error in ['NotRegistered', 'InvalidRegistration']:
                    # Deactivate multiple devices
                    for reg_id in reg_ids:
                        regs[reg_id].deactivate()

        if 'canonical' in resp:
            for reg_id, canonical_id in resp['canonical'].items():
                # Replace registration_id with canonical_id
                device = regs[reg_id]
                device.device_key = canonical_id
                models.db.session.add(device)
                try:
                    # Note: From time to time GCM garbage collects registration
                    #       ids by issuing a new canonical id which replace
                    #       other registration ids for the same device. You
                    #       need to deactivate the devices
                    models.db.session.commit()
                except exc.IntegrityError:
                    models.db.session.rollback()
                    device.deactivate()
        return msg


class APNsNotificationsTask(PushNotificationsTask):

    """Push notifications for APNs."""

    def post(self):  # pylint: disable=no-self-use
        res = self.handle_input(api_args.IOS)
        if isinstance(res, flask.Response):
            return res

        logging.info('Pushing APNs notifications to %s devices',
                     len(flask.request.devices))
        frame = apns.Frame()
        expiry = time.time() + 3600
        priority = 10
        kwargs = api_utils.apns_payload_data(
            flask.request.sender_name, flask.request.message_type)
        payload = apns.Payload(**kwargs)
        for device in flask.request.devices:
            identifier = 1
            frame.add_item(
                device.device_key, payload, identifier, expiry, priority)
        apns_socket = api_utils.create_apns_socket(current_app)
        apns_socket.gateway_server.send_notification_multiple(frame)

        msg = 'Notification to APNs is pushed'
        logging.info(msg)
        return msg


class CleanupiOSDevicesTask(views.MethodView):

    """Cleans up iOS devices."""
    methods = ['GET']

    def get(self):  # pylint: disable=no-self-use
        device_keys = []
        apns_socket = api_utils.create_apns_socket(current_app)
        items_gen = apns_socket.feedback_server.items()
        for device_key, fail_time in items_gen:  # pylint: disable=unused-variable
            device_keys.append(device_key)

        models.Device.deactivate_multiple(device_keys, platform=api_args.IOS)
        msg = 'The following iOS devices are subject to cleanup: {}'.format(
            str(device_keys))
        logging.info(msg)
        return msg


class MailTask(views.MethodView):

    methods = ['POST']

    def post(self):  # pylint: disable=no-self-use
        # XXX: Implement
        return 'ok'


tasks_app.add_url_rule(
    '/push/gcm', view_func=GCMNotificationsTask.as_view('push_gcm'))
tasks_app.add_url_rule(
    '/push/apns', view_func=APNsNotificationsTask.as_view('push_apns'))
tasks_app.add_url_rule(
    '/push/apns/cleanup',
    view_func=CleanupiOSDevicesTask.as_view('cleanup_apns'))
tasks_app.add_url_rule(
    '/mail', view_func=MailTask.as_view('mail'))
