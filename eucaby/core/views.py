
from django.views import generic
from django import http
from django import shortcuts
import logging
import re
from eucaby.eucaby import const
from eucaby.core import models as core_models


class Home(generic.View):

    def get(self, *args, **kwargs):
        return http.HttpResponse('Eucaby rocks')


class ViewLocation(generic.View):

    http_method_names = ['get', ]

    def get(self, *args, **kwargs):
        token = kwargs.get('token')
        logging.info('Token: {}'.format(token))
        # Get session by token
        req = core_models.Request.query(core_models.Request.token==token).get()
        if not req:
            return http.HttpResponseNotFound()
        c = dict(session=req.session.key)
        return shortcuts.render(self.request, 'location.html', c)


class NotifyLocation(generic.View):

    http_method_names = ['post', ]

    def post(self, *args, **kwargs):
        data = self.request.POST
        session = data.get('session', None)
        latlng = data.get('latlng', '')
        if not (session or re.match(const.LATLNG_REGEX, latlng)):
            return http.HttpResponseBadRequest(
                'Invalid latitude, longitude or missing session')
        return http.HttpResponse('Your location has been sent')


