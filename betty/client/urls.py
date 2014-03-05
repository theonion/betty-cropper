from django.conf.urls import patterns, url

urlpatterns = patterns('betty.client.views',
    url(r'^search.html$', 'search'),  # noqa
    url(r'^upload\.html$', 'upload'),
    url(r'^crop\.html$', 'crop'),
)
