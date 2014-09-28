
from django.views import generic
from django import http
from django import shortcuts
import logging
import re
from eucaby.eucaby import const

class Home(generic.View):

    def get(self, *args, **kwargs):
        return http.HttpResponse('Eucaby rocks')


class ViewLocation(generic.View):

    def get(self, *args, **kwargs):

        logging.info('Token: {}'.format(kwargs.get('token')))
        c = {}
        return shortcuts.render(self.request, 'location.html', c) #http.HttpResponse('Your location has been sent')


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


