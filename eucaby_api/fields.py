"""Fields for object serialization."""

from flask_restful import fields as rest_fields

FRIENDS_FIELDS = dict(data=rest_fields.List(rest_fields.Nested(
    dict(username=rest_fields.String(attribute='id'),
         name=rest_fields.String()))))

SESSION_FIELDS = dict(
    key=rest_fields.String,
    sender_username=rest_fields.String,
    recipient_username=rest_fields.String,
    recipient_email=rest_fields.String
)

REQUEST_LOCATION_FIELDS = dict(
    id=rest_fields.Integer,
    token=rest_fields.String,
    type=rest_fields.String(default='request'),
    created_date=rest_fields.DateTime(dt_format='iso8601'),
    session=rest_fields.Nested(SESSION_FIELDS)
)

NOTIFY_LOCATION_FIELDS = dict(
    id=rest_fields.Integer,
    type=rest_fields.String(default='notification'),
    lat=rest_fields.Float(attribute='location.lat'),
    lng=rest_fields.Float(attribute='location.lon'),
    created_date=rest_fields.DateTime(dt_format='iso8601'),
    session=rest_fields.Nested(SESSION_FIELDS)
)

USER_FIELDS = dict(
    username=rest_fields.String,
    first_name=rest_fields.String,
    last_name=rest_fields.String,
    gender=rest_fields.String,
    email=rest_fields.String,
    date_joined=rest_fields.DateTime(dt_format='iso8601')
)
