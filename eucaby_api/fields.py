"""Fields for object serialization."""

from flask_restful import fields as rest_fields

from eucaby_api import models


TOKEN_FIELDS = dict(
    access_token=rest_fields.String,
    token_type=rest_fields.String(default=models.TOKEN_TYPE),
    expires_in=rest_fields.String(default=models.EXPIRATION_SECONDS),
    refresh_token=rest_fields.String,
    scope=rest_fields.String(attribute='scopes')
)
