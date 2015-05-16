
import flask
from flask import views

tasks_app = flask.Blueprint('tasks', __name__)


# Push notifications
class GcmNotificationsView(views.View):
    pass


class ApnsNotificationsView(views.View):
    pass


class CleanupDevicesView(views.View):
    pass


class MailView(views.View):
    pass


tasks_app.add_url_rule(
    '/push/gcm', view_func=GcmNotificationsView.as_view('push_gcm'))
tasks_app.add_url_rule(
    '/push/apns', view_func=ApnsNotificationsView.as_view('push_apns'))
tasks_app.add_url_rule(
    '/push/cleanup', view_func=CleanupDevicesView.as_view('cleanup_devices'))
tasks_app.add_url_rule(
    '/mail', view_func=ApnsNotificationsView.as_view('mail_task'))
