"""Request arguments for API."""

import re
from flask_restful import inputs
from eucaby_api.utils import reqparse


EMAIL_REGEX_PATTERN = '^[A-Z0-9\._%+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}$'  # pylint: disable=anomalous-backslash-in-string
POINT_REGEX_PATTERN = '-?[0-9]+\.?[0-9]*'  # pylint: disable=anomalous-backslash-in-string
LATLNG_REGEX_PATTERN = '^{p},{p}$'.format(p=POINT_REGEX_PATTERN)
EMAIL_REGEX = re.compile(EMAIL_REGEX_PATTERN, flags=re.IGNORECASE)
LATLNG_REGEX = re.compile(LATLNG_REGEX_PATTERN)

MISSING_PARAM = 'Missing {} parameter'
DEFAULT_ERROR = 'Something went wrong'
INVALID_EMAIL = 'Invalid email'
INVALID_LATLNG = 'Missing or invalid latlng parameter'
MISSING_EMAIL_USERNAME = 'Missing email or username parameters'
MISSING_EMAIL_USERNAME_REQ = (
    'Missing token, email or username parameters')
INVALID_ACTIVITY_TYPE = ('Activity type can be either outgoing, incoming, '
                         'request or notification')
INVALID_MESSAGE = 'Message type can be either location or request'
INVALID_PLATFORM = 'Platform can be either android or ios'
INVALID_INT = 'Integer type is expected'
OUTGOING = 'outgoing'
INCOMING = 'incoming'
REQUEST = 'request'
NOTIFICATION = 'notification'
LOCATION = 'location'
ANDROID = 'android'
IOS = 'ios'
ACTIVITY_CHOICES = [OUTGOING, INCOMING, REQUEST, NOTIFICATION]
PLATFORM_CHOICES = [ANDROID, IOS]
MESSAGE_CHOICES = [REQUEST, LOCATION]


class ValidationError(Exception):
    pass


def email(s):
    """Validates email."""
    if EMAIL_REGEX.match(s):
        return s
    raise ValidationError("Invalid email")


def latlng(s):
    """Validates latlng."""
    if LATLNG_REGEX.match(s):
        return s
    raise ValidationError("Latlng should have format: <lat>,<lng>")


def positive_int(v):
    """Validates positive."""
    # Note: There is a similar function in flask_rest/inputs.py:natural
    try:
        v = int(v)
    except ValueError:
        raise ValidationError(INVALID_INT)
    if v < 0:
        raise ValidationError(INVALID_INT)
    return v


REQUEST_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=INVALID_EMAIL),
    reqparse.Argument(name='username', type=str, help=MISSING_EMAIL_USERNAME),
    reqparse.Argument(name='message', type=unicode)
]

NOTIFY_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=INVALID_EMAIL),
    reqparse.Argument(name='username', type=str),
    reqparse.Argument(name='message', type=unicode),
    reqparse.Argument(name='token', type=str),
    reqparse.Argument(name='latlng', type=latlng, required=True,
                      help=INVALID_LATLNG),
]

ACTIVITY_ARGS = [
    reqparse.Argument(name='type', type=str, choices=ACTIVITY_CHOICES,
                      required=True, help=INVALID_ACTIVITY_TYPE),
    reqparse.Argument(name='offset', type=positive_int, default=0,
                      help=INVALID_INT),
    reqparse.Argument(name='limit', type=positive_int, default=50,
                      help=INVALID_INT)
]

SETTINGS_ARGS = [
    reqparse.Argument(name='email_subscription', type=inputs.boolean)
]

REGISTER_DEVICE = [
    reqparse.Argument(name='device_key', type=str, required=True,
                      help=MISSING_PARAM.format('device_key')),
    reqparse.Argument(name='platform', type=str, choices=PLATFORM_CHOICES,
                      required=True, help=INVALID_PLATFORM)
]

PUSH_TASK_ARGS = [
    reqparse.Argument(name='recipient_username', type=str, required=True,
                      help=MISSING_PARAM.format('recipient_username')),
    reqparse.Argument(name='sender_name', type=unicode),
    reqparse.Argument(name='type', type=str, choices=MESSAGE_CHOICES,
                      help=INVALID_MESSAGE)
]
