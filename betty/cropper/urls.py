from django.conf.urls import patterns, url, include

urlpatterns = patterns('betty.cropper.views',
    url(  # noqa
        r'^(?P<id>\d{5,})/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))',
        'redirect_crop'
    ),
    url(  # noqa
        r'^(?P<id>[0-9/]+)/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))',
        'crop'
    ),
    url(r'api/', include("betty.cropper.api.urls"))
)
