
from django.views import generic
from django import http

class Home(generic.View):

    def get(self, *args, **kwargs):
        return http.HttpRequest('Eucaby')


class NotifyLocation(generic.View):

    def get(self, *args, **kwargs):
        print kwargs.get('token')
        return http.HttpRequest('Your location has been sent')


