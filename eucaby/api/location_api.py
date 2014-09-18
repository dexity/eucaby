#import settings
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from core import models as core_models
from api import services
from api import messages as api_messages

package = 'Api'

# Temp
class Greetings(messages.Message):
    text = messages.StringField(1)


@endpoints.api(name='location', version='v1')
class LocationApi(remote.Service):

    REQUEST_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        sender_email=messages.StringField(1),
        receiver_email=messages.StringField(1))

    @endpoints.method(REQUEST_RESOURCE, Greetings,
                      path='/location/request', http_method='POST',
                      name='location.request')
    def request_location(self, request):
        #session = core_models.Session.create(
        #    request.sender_email, request.receiver_email)
        #req = core_models.Request.create(session)

        return Greetings(text='Hello')
        #return api_messages.Request()

application = endpoints.api_server([LocationApi], restricted=False)