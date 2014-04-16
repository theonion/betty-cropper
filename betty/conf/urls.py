try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from .app import settings
from django.conf.urls.static import static

try:
    from django.conf.urls import include, patterns, url
except ImportError:
    # django < 1.5 compat
    from django.conf.urls.defaults import include, patterns, url  # noqa

# TODO: fix up this awful, awful shit.
image_path = urlparse(settings.BETTY_IMAGE_URL).path
if image_path.startswith("/"):
    image_path = image_path[1:]

if image_path != "" and not image_path.endswith("/"):
    image_path += "/"

urlpatterns = patterns('',
    url(r'^{0}'.format(image_path), include("betty.cropper.urls")),  # noqa
    url(r'browser/', include("betty.image_browser.urls")),
    url(r'login/', "django.contrib.auth.views.login")
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
