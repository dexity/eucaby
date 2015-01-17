"""Fields for object serialization."""

from flask_restful import fields as rest_fields

FRIENDS_FIELDS = dict(data=rest_fields.List(rest_fields.Nested(
    dict(username=rest_fields.String(attribute='id'),
         name=rest_fields.String()))))
