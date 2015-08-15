
import datetime
import logging
from django import http
from django import shortcuts
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.views import generic
from django.template import loader

from eucaby.core import forms
from eucaby.core import models
from eucaby_api import args as api_args
from eucaby_api import ndb_models
from eucaby_api.utils import gae as gae_utils


class Home(generic.View):

    def get(self, request):  # pylint: disable=no-self-use
        return shortcuts.render(request, 'index.html')


class Blog(generic.View):

    def get(self, request):
        url = 'http://www.surfingbits.com/blog/2015/eucaby-geo-messenger/'
        return shortcuts.redirect(url)


class Forum(generic.View):

    def get(self, request):
        url = 'https://groups.google.com/d/forum/eucaby'
        return shortcuts.redirect(url)


class About(generic.View):

    def get(self, request):  # pylint: disable=no-self-use
        return shortcuts.render(request, 'about.html')


class Terms(generic.View):

    def get(self, request):  # pylint: disable=no-self-use
        return shortcuts.render(request, 'terms.html')


class Privacy(generic.View):

    def get(self, request):  # pylint: disable=no-self-use
        return shortcuts.render(request, 'privacy.html')


class Feedback(generic.View):

    def get(self, request):  # pylint: disable=no-self-use
        return shortcuts.render(request, 'feedback.html')


def validate_object(request, model_class, uuid, obj_type):
    obj = model_class.get_by_uuid(uuid)
    if not obj:
        raise http.Http404(obj_type + ' not found')

    # Link expires after 1 day
    expiration = obj.created_date + datetime.timedelta(days=1)
    if expiration < datetime.datetime.now():
        context = dict(error=obj_type + ' link has expired')
        return shortcuts.render(request, 'error.html', context)
    return obj


class LocationView(generic.View):

    http_method_names = ['get', ]

    def get(self, request, loc_notif):  # pylint: disable=no-self-use
        context = dict(loc_notif=loc_notif)
        return shortcuts.render(request, 'location.html', context)

    def dispatch(self, request, uuid):  # pylint: disable=arguments-differ
        loc_notif = validate_object(
            request, ndb_models.LocationNotification, uuid, 'Location')
        if isinstance(loc_notif, http.HttpResponse):
            return loc_notif
        return super(LocationView, self).dispatch(request, loc_notif)


class NotifyLocationView(generic.View):

    http_method_names = ['get', 'post']

    def get(self, request, loc_req):  # pylint: disable=no-self-use
        context = dict(loc_req=loc_req)
        return shortcuts.render(request, 'request.html', context)

    def post(self, request, loc_req):  # pylint: disable=no-self-use
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

        # Send notifications to Android and iOS devices
        gae_utils.send_notification(
            loc_req.sender_username, sender_name, api_args.NOTIFICATION,
            loc_notif.id)

        try:
            user = auth_models.User.objects.get(
                username=loc_req.sender_username)
        except auth_models.User.DoesNotExist:
            logging.error('User %s does not exist', loc_req.sender_username)
            return http.JsonResponse(loc_notif.to_dict())

        if models.UserSettings.user_param(user.id, api_args.EMAIL_SUBSCRIPTION):
            # Send email notification to recipient
            eucaby_url = settings.EUCABY_URL
            location_url = '{}/location/{}'.format(eucaby_url, loc_notif.uuid)
            context = dict(
                sender_name=sender_name, recipient_name=loc_req.sender_name,
                eucaby_url=eucaby_url, location_url=location_url,
                message=data['message'])
            body = loader.render_to_string(
                'mail/location_response_body.txt', context)
            gae_utils.send_mail('New Location', body, [user.email])

        return http.JsonResponse(loc_notif.to_dict())

    def dispatch(self, request, uuid):  # pylint: disable=arguments-differ
        loc_req = validate_object(
            request, ndb_models.LocationRequest, uuid, 'Request')
        if isinstance(loc_req, http.HttpResponse):
            return loc_req
        return super(NotifyLocationView, self).dispatch(request, loc_req)
