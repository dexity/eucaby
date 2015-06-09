
from google.appengine.ext import ndb
from django.conf import settings
from django.views import generic
from django import http
from django import shortcuts
import json
import logging
import re
import redis
from eucaby.eucaby import const
from eucaby.core import models as core_models


class Home(generic.View):

    def get(self, *args, **kwargs):
        return http.HttpResponse('Eucaby rocks')


class LocationView(generic.View):

    http_method_names = ['get', ]

    def get(self, *args, **kwargs):
        token = kwargs.get('token')
        logging.info('Token: {}'.format(token))
        # Get session by token
        req = core_models.Request.query(
            core_models.Request.token == token).get()
        if not req:
            return http.HttpResponseNotFound()
        c = dict(session=req.session.key)
        return shortcuts.render(self.request, 'location.html', c)


class NotifyLocationView(generic.View):

    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        data = self.request.POST
        _session = data.get('session', None)
        latlng = data.get('latlng', '')
        if not (_session or re.match(const.LATLNG_REGEX, latlng)):
            return http.HttpResponseBadRequest(
                'Invalid latitude, longitude or missing session')

        session = core_models.Session.query(
            core_models.Session.key == _session).get()
        if not session:
            return http.HttpResponseNotFound('Session does not exist')
        resp = core_models.Response.query(
            core_models.Response.session == session).get()
        if resp:    # Update response
            resp.location = ndb.GeoPt(latlng)
            resp.put()
        else:
            resp = core_models.Response.create(session, latlng)
        # Post to location channel
        r = redis.StrictRedis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        r.publish('eucabyrt', json.dumps(resp.to_dict()))

        return http.HttpResponse(
            json.dumps(dict(message='Your location has been sent')),
            mimetype='application/json')


