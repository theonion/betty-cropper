from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'betty.views.index'),  # noqa
    url(r'^upload\.html', 'betty.views.upload'),
    url(r'^api/new$', 'betty.api.new'),
    url(r'^api/search$', 'betty.api.search'),
    url(r'^api/(?P<image_id>\d+)/(?P<ratio_slug>[a-z0-9]+)$', 'betty.api.update_selection'),
    url(r'^api/(?P<image_id>\d+)$', 'betty.api.detail'),
    url(
        r'^(?P<id>[0-9/]+)/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))',
        'betty.views.crop'
    ),
)
