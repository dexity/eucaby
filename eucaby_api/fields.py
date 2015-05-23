"""Fields for object serialization."""

from flask_restful import fields as rest_fields
from eucaby_api.utils import fields as utils_fields

REQUEST = 'request'
NOTIFICATION = 'notification'

INDEX_FIELDS = dict(message=rest_fields.String)

FRIENDS_FIELDS = dict(
    data=rest_fields.List(rest_fields.Nested(
        dict(username=rest_fields.String(attribute='id'),
             name=rest_fields.String()))))

SENDER_FIELDS = dict(
    username=rest_fields.String,
    name=rest_fields.String)

RECIPIENT_FIELDS = SENDER_FIELDS.copy()
RECIPIENT_FIELDS.update(dict(email=rest_fields.String))

LOCATION_FIELDS = dict(
    lat=rest_fields.Float,
    lng=rest_fields.Float(attribute='lon'))

SESSION_FIELDS = dict(
    token=rest_fields.String,
    complete=rest_fields.Boolean)

MESSAGE_FIELDS = dict(
    id=rest_fields.Integer,
    type=rest_fields.String(default=REQUEST),
    message=rest_fields.String(),
    sender=rest_fields.Nested(SENDER_FIELDS),
    recipient=rest_fields.Nested(RECIPIENT_FIELDS),
    created_date=utils_fields.IsoDateTime(),
    session=rest_fields.Nested(SESSION_FIELDS))

REQUEST_FIELDS = MESSAGE_FIELDS.copy()

NOTIFICATION_FIELDS = MESSAGE_FIELDS.copy()
NOTIFICATION_FIELDS.update(dict(
    type=rest_fields.String(default=NOTIFICATION),
    location=rest_fields.Nested(LOCATION_FIELDS)))

INLINE_REQUEST_FIELDS = REQUEST_FIELDS.copy()
INLINE_REQUEST_FIELDS.pop('type')
INLINE_REQUEST_FIELDS.pop('session')

INLINE_NOTIFICATION_FIELDS = NOTIFICATION_FIELDS.copy()
INLINE_NOTIFICATION_FIELDS.pop('type')
INLINE_NOTIFICATION_FIELDS.pop('session')

DETAIL_REQUEST_FIELDS = REQUEST_FIELDS.copy()
DETAIL_REQUEST_FIELDS['notifications'] = rest_fields.List(
    rest_fields.Nested(INLINE_NOTIFICATION_FIELDS))

DETAIL_NOTIFICATION_FIELDS = NOTIFICATION_FIELDS.copy()
DETAIL_NOTIFICATION_FIELDS['request'] = rest_fields.Nested(
    INLINE_REQUEST_FIELDS, allow_null=True)

USER_FIELDS = dict(
    username=rest_fields.String,
    name=rest_fields.String,
    first_name=rest_fields.String,
    last_name=rest_fields.String,
    gender=rest_fields.String,
    email=rest_fields.String,
    date_joined=utils_fields.IsoDateTime())

SETTINGS_FIELDS = dict(
    email_subscription=rest_fields.Boolean
)

REQUEST_LIST_FIELDS = dict(
    data=rest_fields.List(rest_fields.Nested(
        REQUEST_FIELDS)))

NOTIFICATION_LIST_FIELDS = dict(
    data=rest_fields.List(rest_fields.Nested(
        NOTIFICATION_FIELDS)))

DEVICE_FIELDS = dict(
    platform=rest_fields.String,
    device_key=rest_fields.String,
    created_date=utils_fields.IsoDateTime(),
    active=rest_fields.Boolean)
