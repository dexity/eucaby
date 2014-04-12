
from django.conf.urls import *

urlpatterns = patterns('core.views',
    url(r'^$', "index"),
    url(r'^node_location$', "node_location")
)


