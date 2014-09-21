
from google.appengine.api import mail as gae_mail


def send_mail(subject, message, from_email, recipient_list):
    gae_mail.send_mail(
        sender=from_email, to=recipient_list, subject=subject, body=message)