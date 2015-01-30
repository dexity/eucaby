"""Fields for object serialization."""

from flask_restful import fields as rest_fields

FRIENDS_FIELDS = dict(
    data=rest_fields.List(rest_fields.Nested(
        dict(username=rest_fields.String(attribute='id'),
             name=rest_fields.String()))))

SENDER_FIELDS = dict(
    username=rest_fields.String,
    name=rest_fields.String)

RECIPIENT_FIELDS = SENDER_FIELDS.copy()
RECIPIENT_FIELDS.update(dict(email=rest_fields.String))

SESSION_FIELDS = dict(
    key=rest_fields.String,
    complete=rest_fields.Boolean)

REQUEST_FIELDS = dict(
    id=rest_fields.Integer,
    type=rest_fields.String(default='request'),
    sender=rest_fields.Nested(SENDER_FIELDS),
    recipient=rest_fields.Nested(RECIPIENT_FIELDS),
    created_date=rest_fields.DateTime(dt_format='iso8601'),
    session=rest_fields.Nested(SESSION_FIELDS))

NOTIFICATION_FIELDS = REQUEST_FIELDS.copy()
NOTIFICATION_FIELDS.update(dict(
    type=rest_fields.String(default='notification'),
    lat=rest_fields.Float(attribute='location.lat'),
    lng=rest_fields.Float(attribute='location.lon')))

USER_FIELDS = dict(
    username=rest_fields.String,
    first_name=rest_fields.String,
    last_name=rest_fields.String,
    gender=rest_fields.String,
    email=rest_fields.String,
    date_joined=rest_fields.DateTime(dt_format='iso8601'))

REQUEST_LIST_FIELDS = dict(
    data=rest_fields.List(rest_fields.Nested(
        REQUEST_FIELDS)))

NOTIFICATION_LIST_FIELDS = dict(
    data=rest_fields.List(rest_fields.Nested(
        NOTIFICATION_FIELDS)))
