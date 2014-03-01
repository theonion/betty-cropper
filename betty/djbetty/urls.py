from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^api/new$', 'betty.djbetty.api.new'),  # noqa
    url(r'^api/search$', 'betty.djbetty.api.search'),
    url(r'^api/(?P<image_id>\d+)/(?P<ratio_slug>[a-z0-9]+)$', 'betty.djbetty.api.update_selection'),
    url(r'^api/(?P<image_id>\d+)$', 'betty.djbetty.api.detail'),
    url(
        r'^(?P<id>[0-9/]+)/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))',
        'betty.djbetty.views.crop'
    ),
)
