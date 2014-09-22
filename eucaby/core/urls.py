
from django.conf import urls
from eucaby.core import views

urlpatterns = urls.patterns('',

    urls.url(r'^$', views.Home.as_view(), name='home'),
    urls.url(r'^(?P<token>(\d{32}))$', views.NotifyLocation.as_view(),
             name='notify_location'),
)