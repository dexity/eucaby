from django.conf import urls

# from django.contrib import admin
# admin.autodiscover()

urlpatterns = urls.patterns('',
    urls.url(r'', urls.include('eucaby.core.urls')),

    # url(r'^admin/', include(admin.site.urls)),
)
