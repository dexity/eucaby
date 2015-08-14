
from django.conf import urls
from eucaby.core import views

UUID_REGEX = '[0-9a-f]{32}'

urlpatterns = urls.patterns(
    '',
    urls.url(r'^$', views.Home.as_view(), name='home'),
    urls.url(r'^blog$', views.Blog.as_view(), name='blog'),
    urls.url(r'^forum$', views.Forum.as_view(), name='forum'),
    urls.url(r'^terms$', views.Terms.as_view(), name='terms'),
    urls.url(r'^privacy$', views.Privacy.as_view(), name='privacy'),
    urls.url(r'^location/(?P<uuid>({}))$'.format(UUID_REGEX),
             views.LocationView.as_view(), name='view_location'),
    urls.url(r'^request/(?P<uuid>({}))$'.format(UUID_REGEX),
             views.NotifyLocationView.as_view(), name='notify_location')
    # urls.url(r'^about$', views.About.as_view(), name='about'),
    # urls.url(r'^feedback$', views.Feedback.as_view(), name='feedback'),
)
