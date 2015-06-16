
from google.appengine.ext import ndb
from django.conf import settings
from django.views import generic
from django.views.generic import edit as edit_views
from django import http
from django import shortcuts
import json
import datetime
import logging
import re
import redis
from eucaby.eucaby import const
from eucaby.core import models as core_models
from eucaby.core import forms
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
        form = forms.LocationForm(request.POST)
        if not form.is_valid():
            msg = 'Something went wrong'
            if 'lat' in form.errors or 'lng' in form.errors:
                msg = 'Invalid location'
            elif 'message' in form.errors:
                msg = form.errors['message'][0]
            resp = http.JsonResponse(dict(error=msg))
            resp.status_code = 400
            return resp

        data = form.cleaned_data
        default_name = loc_req.recipient_email or 'Unknown user'
        sender_username = loc_req.recipient_username or default_name
        sender_name = loc_req.recipient_name or default_name

        loc_notif = ndb_models.LocationNotification.create(
            '{lat},{lng}'.format(**data), sender_username, sender_name,
            recipient_username=loc_req.sender_username,
            recipient_name=loc_req.sender_name, message=data['message'],
            is_web=True, session=loc_req.session)
        return http.JsonResponse(loc_notif.to_dict())

    def dispatch(self, request, uuid):
        loc_req = validate_object(
            request, ndb_models.LocationRequest, uuid, 'Request')
        if isinstance(loc_req, http.HttpResponse):
            return loc_req
        return super(NotifyLocationView, self).dispatch(request, loc_req)
