"""Fields for object serialization."""

from flask_restful import fields as rest_fields

FRIENDS_FIELDS = dict(data=rest_fields.List(rest_fields.Nested(
    dict(username=rest_fields.String(attribute='id'),
         name=rest_fields.String()))))

REQUEST_LOCATION_FIELDS = dict(
    id=rest_fields.String(attribute='token'),
    created_date=rest_fields.DateTime()
)

# class Session(messages.Message):
#     key = messages.StringField(1, required=True)
#     sender_email = messages.StringField(2, required=True)
#     receiver_email = messages.StringField(3, required=True)
#
#
# class Request(messages.Message):
#     token = messages.StringField(1, required=True)
#     session = messages.MessageField(Session, 2, required=True)
#     created_date = messages.StringField(3, required=True)
