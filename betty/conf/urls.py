import urlparse

from .app import settings
from django.conf.urls.static import static

try:
    from django.conf.urls import include, patterns, url
except ImportError:
    # django < 1.5 compat
    from django.conf.urls.defaults import include, patterns, url  # noqa
from django.contrib import admin
# from django.views.defaults import page_not_found

admin.autodiscover()
# admin_media_dir = os.path.join(os.path.dirname(admin.__file__), 'media')


# handler404 = lambda x: page_not_found(x, template_name='sentry/404.html')


# def handler500(request):
#     """
#     500 error handler.

#     Templates: `500.html`
#     Context: None
#     """
#     from django.template import Context, loader
#     from django.http import HttpResponseServerError

#     context = {'request': request}

#     t = loader.get_template('sentry/500.html')
#     return HttpResponseServerError(t.render(Context(context)))

image_path = urlparse.urlparse(settings.BETTY_IMAGE_URL).path
if image_path.startswith("/"):
    image_path = image_path[1:]


urlpatterns = patterns('',
    url(r'^{0}'.format(image_path), include("betty.server.urls")),  # noqa
    url(r'login/', "django.contrib.auth.views.login")
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
