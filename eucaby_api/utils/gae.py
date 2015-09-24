# Google AppEngine utils

import logging
from google.appengine.api import taskqueue


def send_notification(
        recipient_username, sender_name, message_type, message_id):
    """Sends notifications to Android and iOS devices."""
    logging.info(
        '%s %s sent from %s to %s', message_type.capitalize(), message_id,
        sender_name, recipient_username)
    params = dict(
        recipient_username=recipient_username, sender_name=sender_name,
        message_type=message_type, message_id=message_id)
    taskqueue.add(queue_name='push', url='/tasks/push/gcm', params=params)
    taskqueue.add(queue_name='push', url='/tasks/push/apns', params=params)


def send_mail(subject, body, recipient_list):
    """Sends email with task queue."""
    params = dict(subject=subject, body=body, recipient=recipient_list)
    taskqueue.add(queue_name='mail', url='/tasks/mail', params=params)
