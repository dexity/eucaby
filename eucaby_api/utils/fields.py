from flask_restful import fields as rest_fields


class IsoDateTime(rest_fields.Raw):
    """Date time in ISO-8601 format.

    Note: flask_restful DateTime timezone is broken in ISO-8601 format
    """

    def format(self, value):
        try:
            return value.isoformat()
        except AttributeError as e:
            raise rest_fields.MarshallingException(e)
