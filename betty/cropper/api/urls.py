from django.conf.urls import patterns, url

urlpatterns = patterns('betty.cropper.api.views',
    url(r'^new$', 'new'),  # noqa
    url(r'^search$', 'search'),
    url(r'^(?P<image_id>\d+)/(?P<ratio_slug>[a-z0-9]+)$', 'update_selection'),
    url(r'^(?P<image_id>\d+)$', 'detail'),
)
