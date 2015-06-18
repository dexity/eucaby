# Google AppEngine utils

import logging
from google.appengine.api import taskqueue


def send_notification(recipient_username, sender_name, message_type):
    """Sends notifications to Android and iOS devices."""
    logging.info('%s notification sent from %s to %s',
                 message_type.capitalize(), sender_name, recipient_username)
    params = dict(
        recipient_username=recipient_username,
        sender_name=sender_name, type=message_type)
    taskqueue.add(queue_name='push', url='/tasks/push/gcm', params=params)
    taskqueue.add(queue_name='push', url='/tasks/push/apns', params=params)
