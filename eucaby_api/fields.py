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
    id=rest_fields.String(attribute='token'),
    created_date=rest_fields.DateTime(dt_format='iso8601'),
    session=rest_fields.Nested(SESSION_FIELDS)
)

NOTIFY_LOCATION_FIELDS = dict(
    lat=rest_fields.String,
    lng=rest_fields.String,
    created_date=rest_fields.DateTime(dt_format='iso8601'),
    session=rest_fields.Nested(SESSION_FIELDS)
)
