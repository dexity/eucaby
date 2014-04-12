import random
import redis
import json
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from .models import UserLocation

@login_required
def index(request):
    return render(request, "core/index.html", {})


@require_POST
@csrf_exempt
def node_location(request):
    tl = settings.TOP_LEFT
    br = settings.BOTTOM_RIGHT
    lat = random.uniform(br[0], tl[0])
    lng = random.uniform(br[1], tl[1])

    try:
        session = Session.objects.get(session_key=request.POST.get('sessionid'))
        user_id = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=user_id)
    except (Session.DoesNotExist, User.DoesNotExist):
        return HttpResponseBadRequest("fail")

    loc = UserLocation(user=user, lat=lat, lng=lng)
    loc.save()  # Save location

    resp = dict(lat=lat, lng=lng, username=user.username)
    # Post to location channel
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    r.publish('realtaxi', json.dumps(resp))

    return HttpResponse("ok")

