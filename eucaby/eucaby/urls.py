from django.conf import urls
from django.conf import settings

urlpatterns = urls.patterns(
    '',
    urls.url(r'', urls.include('eucaby.core.urls')),
)

if settings.DEBUG:
    urlpatterns += urls.patterns(
        '',
        urls.url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        urls.url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
    )
