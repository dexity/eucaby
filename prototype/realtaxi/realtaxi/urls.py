from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^', include("core.urls")),
    url(r'^api/', include("api.urls")),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout')
)

