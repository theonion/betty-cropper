from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^api/new$', 'betty.server.api.new'),  # noqa
    url(r'^api/search$', 'betty.server.api.search'),
    url(r'^api/(?P<image_id>\d+)/(?P<ratio_slug>[a-z0-9]+)$', 'betty.server.api.update_selection'),
    url(r'^api/(?P<image_id>\d+)$', 'betty.server.api.detail'),
    url(
        r'^(?P<id>[0-9/]+)/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))',
        'betty.server.views.crop'
    ),
)
