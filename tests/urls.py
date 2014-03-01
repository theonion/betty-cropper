from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    url(r'^images/', include("betty.urls")),  # noqa
)
