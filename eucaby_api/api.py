import logging

import endpoints
from protorpc import remote
from eucaby.core import models as core_models
from eucaby_api import messages as api_messages
from eucaby.utils import mail as utils_mail
from eucaby_api import resources as api_resources


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
        kwargs = req.to_dict()
        logging.info(kwargs)
        return api_messages.Request(**kwargs)

    @endpoints.method(
        endpoints.ResourceContainer(api_resources.LocationResource),
        api_messages.Response, path='location/notify', http_method='POST',
        name='location.notify')
    def notify_location(self, request):
        session = core_models.Session.create(
            request.sender_email, request.receiver_email)
        resp = core_models.Response.create(session, request.latlng)
        kwargs = resp.to_dict()
        logging.info(kwargs)
        return api_messages.Response(**kwargs)


application = endpoints.api_server([EucabyApi], restricted=False)

