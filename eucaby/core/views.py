
from django.views import generic
from django import http
import logging

class Home(generic.View):

    def get(self, *args, **kwargs):
        return http.HttpResponse('Eucaby rocks')


class NotifyLocation(generic.View):

    def get(self, *args, **kwargs):
        logging.info('Token: {}'.format(kwargs.get('token')))
        return http.HttpResponse('Your location has been sent')


