
from django.conf import urls
from eucaby.core import views

urlpatterns = urls.patterns('',
    urls.url(r'^$', views.Home.as_view(), name='home'),
    urls.url(r'^/location/(?P<token>([0-9a-f]{32}))$',
             views.LocationView.as_view(), name='view_location'),
    urls.url(r'^/request/(?P<token>([0-9a-f]{32}))$',
             views.NotifyLocationView.as_view(), name='notify_location'))
