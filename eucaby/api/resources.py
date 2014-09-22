from protorpc import messages
from eucaby.api import messages as api_messages


class RequestResource(messages.Message):
    sender_email = messages.StringField(1, required=True)
    receiver_email = messages.StringField(2, required=True)


class LocationResource(messages.Message):
    latlng=api_messages.LatLngField(1, required=True)
    sender_email=messages.StringField(2, required=True)
    receiver_email=messages.StringField(3, required=True)