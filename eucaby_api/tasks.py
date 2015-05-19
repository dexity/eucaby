
import apns
import flask
from flask import views
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

    """Push notifications for GCM and APNs."""
    methods = ['POST']

    def post(self):
        # 'recipient_username', 'sender_username', 'devices'
        username = flask.request.form.get('recipient_username')
        if not username:
            return 'Missing recipient_username parameter', 400
        devices = models.Device.get_by_user(username)
        if not devices:
            return 'User device not found', 404
        msg = 'New incoming messages'

        ios_tokens = []
        android_reg_ids = []
        for device in devices:
            if device.platform == api_args.ANDROID:
                android_reg_ids.append(device.device_key)
            elif device.platform == api_args.IOS:
                ios_tokens.append(device.device_key)

        # GCM
        # !!! Prototype

        import urllib2
        import json
        API_KEY = 'AIzaSyApFKUOZoJffYaeD_TjvPKjORWp1JiBdMc'
        headers = {
            'Authorization': 'key=' + API_KEY,
            'Content-Type': 'application/json'
        }
        url = 'https://android.googleapis.com/gcm/send'
        data = {
            'registration_ids': android_reg_ids,
            'data': {
                'title': 'Eucaby',
                'message': msg
            }
        }
        data = json.dumps(data)

        req = urllib2.Request(url, data, headers)
        resp = urllib2.urlopen(req)
        print resp.read()

        # APNs
        # XXX: Handle properly multiple messages
        for token in ios_tokens:
            payload = apns.Payload(alert=msg, sound="default")
            apns_socket.gateway_server.send_notification(token, payload)

        # XXX: If NotRegistered error, cleanup in cleanup queue

        return OK


class CleanupDevicesTask(views.View):
    pass


class MailTask(views.View):
    pass


tasks_app.add_url_rule(
    '/push', view_func=PushNotificationsTask.as_view('push'))
tasks_app.add_url_rule(
    '/push/cleanup', view_func=CleanupDevicesTask.as_view('cleanup_devices'))
tasks_app.add_url_rule(
    '/mail', view_func=MailTask.as_view('mail'))
