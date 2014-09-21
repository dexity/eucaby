#import settings
import endpoints
import logging
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from eucaby.core import models as core_models
from eucaby.api import services
from eucaby.api import messages as api_messages

package = 'Eucaby'


@endpoints.api(name='eucaby', version='v1')
class LocationApi(remote.Service):

    REQUEST_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        sender_email=messages.StringField(1, required=True),
        receiver_email=messages.StringField(2, required=True))

    LOCATION_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        latlng=api_messages.LatLngField(1, required=True),
        sender_email=messages.StringField(2, required=True),
        receiver_email=messages.StringField(3, required=True))

    @endpoints.method(REQUEST_RESOURCE, api_messages.Request,
                      path='location/request', http_method='POST',
                      name='location.request')
    def request_location(self, request):
        session = core_models.Session.create(
            request.sender_email, request.receiver_email)
        req = core_models.Request.create(session)
        return api_messages.Request(**req.to_dict())

    @endpoints.method(LOCATION_RESOURCE, api_messages.Response,
                      path='location/notify', http_method='POST',
                      name='location.notify')
    def notify_location(self, request):
        session = core_models.Session.create(
            request.sender_email, request.receiver_email)
        resp = core_models.Response.create(session, request.latlng)
        return api_messages.Response(**resp.to_dict())

application = endpoints.api_server([LocationApi], restricted=False)

