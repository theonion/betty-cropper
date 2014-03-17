from django.conf.urls import patterns, url

urlpatterns = patterns('betty.image_browser.views',
    url(r'^search.html$', 'search'),  # noqa
    url(r'^upload\.html$', 'upload'),
    url(r'^crop\.html$', 'crop'),
)
