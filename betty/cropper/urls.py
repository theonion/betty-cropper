from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    'betty.cropper.views',
    url(r'^image\.js$', "image_js"),
    url(r'^(?P<id>\d{5,})/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))$',
        'redirect_crop'),
    url(r'^(?P<id>[0-9/]+)/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))$',
        'crop'),
    url(r'^(?P<id>[0-9/]+)/animated/original\.(?P<extension>(jpg|gif))$',
        'animated'),
    url(r'^api/', include("betty.cropper.api.urls")),
)
