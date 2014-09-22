
import endpoints
import logging
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from eucaby.core import models as core_models
from eucaby.api import messages as api_messages
from eucaby.api import resources as api_resources
from eucaby.utils import mail as utils_mail

package = 'Eucaby'


@endpoints.api(name='eucaby', version='v1')
class EucabyApi(remote.Service):

    @endpoints.method(
        endpoints.ResourceContainer(api_resources.RequestResource),
        api_messages.Request, path='location/request', http_method='POST',
        name='location.request')
    def request_location(self, request):
        session = core_models.Session.create(
            request.sender_email, request.receiver_email)
        req = core_models.Request.create(session)

        NOREPLY_EMAIL = 'alex@eucaby.com'
        MSG = """
        You received location request from user {}.
        Follow the link to notify your location:
        {}
        """.format(request.sender_email,
                   'http://eucaby-dev.appspot.com/{}'
                   .format(req.token))

        utils_mail.send_mail(
            'Location Request', MSG, NOREPLY_EMAIL, [request.receiver_email])
        return api_messages.Request(**req.to_dict())

    @endpoints.method(
        endpoints.ResourceContainer(api_resources.LocationResource),
        api_messages.Response, path='location/notify', http_method='POST',
        name='location.notify')
    def notify_location(self, request):
        session = core_models.Session.create(
            request.sender_email, request.receiver_email)
        resp = core_models.Response.create(session, request.latlng)
        return api_messages.Response(**resp.to_dict())


application = endpoints.api_server([EucabyApi], restricted=False)

