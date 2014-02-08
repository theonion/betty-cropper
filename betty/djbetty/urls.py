from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^api/new$', 'betty.djbetty.api.new'),
    
    url(r'^(?P<id>[0-9/]+)/(?P<ratio_slug>[a-z0-9]+)/(?P<width>\d+)\.(?P<extension>(jpg|png))', 'betty.djbetty.views.crop'),
)