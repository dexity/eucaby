
import apns
import flask
from flask import views
from flask import current_app
from gcm import gcm
import logging
import os
from sqlalchemy import exc

from eucaby_api import args as api_args
from eucaby_api import models
from eucaby_api.utils import reqparse
from eucaby_api.utils import utils as api_utils


tasks_app = flask.Blueprint('tasks', __name__)


def create_apns_socket():
    """Creates socket for APNs service."""
    return apns.APNs(
        use_sandbox=True, cert_file=os.path.abspath('private/EucabyCert.pem'),
        key_file=os.path.abspath('private/EucabyKey.pem'))


apns_socket = create_apns_socket()


class PushNotificationsTask(views.MethodView):

    pass


class GCMNotificationsTask(views.MethodView):

    """Push notifications for GCM."""
    methods = ['POST']

    def post(self):  # pylint: disable=no-self-use
        args = reqparse.clean_args(api_args.GCM_TASK_ARGS, is_task=True)
        if isinstance(args, flask.Response):
            logging.error(str(args.data))
            return args

        recipient_username = args['recipient_username']
        sender_name = args['sender_name']
        msg_type = args['type']

        devices = models.Device.get_by_username(
            recipient_username, platform=api_args.ANDROID)
        if not devices:
            msg = 'User device not found'
            logging.info(msg)
            return msg

        regs = {}
        for dev in devices:
            regs[dev.device_key] = dev

        data = api_utils.gcm_payload_data(sender_name, msg_type)
        gcm_app = gcm.GCM(current_app.config['GCM_API_KEY'])
        try:
            resp = gcm_app.json_request(
                registration_ids=regs.keys(), data=data, retries=7)
        except gcm.GCMException as e:
            logging.error(
                'Failed to push notification. %s: %s',
                e.__class__.__name__, e.message)
            return e.message, 500

        msg = 'GCM result: {}'.format(str(resp))
        logging.debug(msg)
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


class APNsNotificationsTask(views.MethodView):

    """Push notifications for APNs."""
    methods = ['POST']

    def post(self):  # pylint: disable=no-self-use
        # XXX: Handle properly multiple messages
        # ios_tokens = []
        # for token in ios_tokens:
        #     payload = apns.Payload(alert=msg, sound="default")
        #     apns_socket.gateway_server.send_notification(token, payload)

        return 'ok'


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
    '/mail', view_func=MailTask.as_view('mail'))
