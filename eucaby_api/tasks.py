
import apns
import flask
from flask import views
from flask import current_app
from gcm import gcm
import logging
import os

from eucaby_api import args as api_args
from eucaby_api import models


tasks_app = flask.Blueprint('tasks', __name__)

OK = 'ok'


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

    def post(self):
        username = flask.request.form.get('recipient_username')
        if not username:
            return 'Missing recipient_username parameter', 400
        devices = models.Device.get_by_username(username, platform=api_args.ANDROID)
        if not devices:
            return 'User device not found', 404

        regs = {}
        for dev in devices:
            regs[dev.device_key] = dev

        data = dict(title='Eucaby', message='New incoming messages')
        gcm_app = gcm.GCM(current_app.config['GCM_API_KEY'])
        try:
            resp = gcm_app.json_request(
                registration_ids=regs.keys(), data=data, retries=7)
        except gcm.GCMException as e:
            logging.error('Failed to push notification. {}: {}'.format(
                e.__class__.__name__, e.message))
            return e.message, 500

        commit = False
        if 'errors' in resp:
            for error, reg_ids in resp['errors'].items():
                if error in ['NotRegistered', 'InvalidRegistration']:
                    # Deactivate multiple devices
                    for reg_id in reg_ids:
                        regs[reg_id].deactivate(commit=False)
                        commit = True

        if 'canonical' in resp:
            for reg_id, canonical_id in resp['canonical'].items():
                # Replace registration_id with canonical_id
                device = regs[reg_id]
                device.device_key = canonical_id
                models.db.session.add(device)
                commit = True
        if commit:
            models.db.session.commit()
        return OK


class APNsNotificationsTask(views.MethodView):

    """Push notifications for APNs."""
    methods = ['POST']

    def post(self):
        # XXX: Handle properly multiple messages
        # ios_tokens = []
        # for token in ios_tokens:
        #     payload = apns.Payload(alert=msg, sound="default")
        #     apns_socket.gateway_server.send_notification(token, payload)

        return OK


class MailTask(views.View):
    pass


tasks_app.add_url_rule(
    '/push/gcm', view_func=GCMNotificationsTask.as_view('push_gcm'))
tasks_app.add_url_rule(
    '/push/apns', view_func=APNsNotificationsTask.as_view('push_apns'))
tasks_app.add_url_rule(
    '/mail', view_func=MailTask.as_view('mail'))
