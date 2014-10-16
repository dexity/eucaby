
import endpoints
from protorpc import messages
import re

from eucaby.eucaby import const

# Messages
class GeoPtMessage(messages.Message):
    lat = messages.FloatField(1, required=True)
    lng = messages.FloatField(2, required=True)


class Session(messages.Message):
    key = messages.StringField(1, required=True)
    sender_email = messages.StringField(2, required=True)
    receiver_email = messages.StringField(3, required=True)


class Request(messages.Message):
    token = messages.StringField(1, required=True)
    session = messages.MessageField(Session, 2, required=True)
    created_date = messages.StringField(3, required=True)


class Response(messages.Message):
    location = messages.MessageField(GeoPtMessage, 1, required=True)
    session = messages.MessageField(Session, 2, required=True)
    created_date = messages.StringField(3, required=True)


# Message fields
class LatLngField(messages.StringField):

    def validate_element(self, value):
        if not value or not re.match(const.LATLNG_REGEX, value):
            raise endpoints.BadRequestException(
                'Wrong format. Latitude and longitude should have format: '
                '<lat>,<lng>')
        super(LatLngField, self).validate_element(value)