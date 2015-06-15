
from google.appengine.ext import ndb
from django.conf import settings
from django.views import generic
from django import http
from django import shortcuts
import json
import datetime
import logging
import re
import redis
from eucaby.eucaby import const
from eucaby.core import models as core_models
from eucaby_api import ndb_models


class Home(generic.View):

    def get(self, request):
        return shortcuts.render(request, 'index.html')


class About(generic.View):

    def get(self, request):
        return shortcuts.render(request, 'about.html')


class Terms(generic.View):

    def get(self, request):
        return shortcuts.render(request, 'terms.html')

class Privacy(generic.View):

    def get(self, request):
        return shortcuts.render(request, 'privacy.html')

class Feedback(generic.View):

    def get(self, request):
        return shortcuts.render(request, 'feedback.html')


def validate_object(request, model_class, uuid, obj_type):
    obj = model_class.get_by_uuid(uuid)
    if not obj:
        raise http.Http404(obj_type + ' not found')

    # Link expires after 1 day
    expiration = obj.created_date + datetime.timedelta(days=1)
    if expiration < datetime.datetime.now():
        c = dict(error=obj_type + ' link has expired')
        return shortcuts.render(request, 'error.html', c)
    return obj


class LocationView(generic.View):

    http_method_names = ['get', ]

    def get(self, request, loc_notif):
        c = dict(loc_notif=loc_notif)
        return shortcuts.render(request, 'location.html', c)

    def dispatch(self, request, uuid):
        loc_notif = validate_object(
            request, ndb_models.LocationNotification, uuid, 'Location')
        if isinstance(loc_notif, http.HttpResponse):
            return loc_notif
        return super(LocationView, self).dispatch(request, loc_notif)


class NotifyLocationView(generic.View):

    http_method_names = ['get', 'post']

    def get(self, request, loc_req):
        c = dict(loc_req=loc_req)
        return shortcuts.render(request, 'request.html', c)


    def post(self, request, loc_req):

        pass


#     def post(self, *args, **kwargs):
#         data = self.request.POST
#         _session = data.get('session', None)
#         latlng = data.get('latlng', '')
#         if not (_session or re.match(const.LATLNG_REGEX, latlng)):
#             return http.HttpResponseBadRequest(
#                 'Invalid latitude, longitude or missing session')
#
#         session = core_models.Session.query(
#             core_models.Session.key == _session).get()
#         if not session:
#             return http.HttpResponseNotFound('Session does not exist')
#         resp = core_models.Response.query(
#             core_models.Response.session == session).get()
#         if resp:    # Update response
#             resp.location = ndb.GeoPt(latlng)
#             resp.put()
#         else:
#             resp = core_models.Response.create(session, latlng)
#         # Post to location channel
#         r = redis.StrictRedis(
#             host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
#         r.publish('eucabyrt', json.dumps(resp.to_dict()))
#
#         return http.HttpResponse(
#             json.dumps(dict(message='Your location has been sent')),
#             mimetype='application/json')

    def dispatch(self, request, uuid):
        loc_req = validate_object(
            request, ndb_models.LocationRequest, uuid, 'Request')
        if isinstance(loc_req, http.HttpResponse):
            return loc_req
        return super(NotifyLocationView, self).dispatch(request, loc_req)
