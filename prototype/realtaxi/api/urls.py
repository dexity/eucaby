
from django.conf.urls import *

urlpatterns = patterns('api.views',
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^auth/token', 'rest_framework.authtoken.views.obtain_auth_token'), # Get token for user's credentials
)
