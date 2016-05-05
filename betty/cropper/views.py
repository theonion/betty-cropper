import json
from betty.conf.app import settings

from django.http import (Http404, HttpResponse, HttpResponseNotModified,
                         HttpResponseServerError, HttpResponseRedirect)
from django.shortcuts import render
from django.utils.cache import patch_cache_control
from django.utils.http import http_date

from django.views.decorators.cache import cache_control
from six.moves import urllib

from .models import Image, Ratio
from .utils.http import check_not_modified
from .utils.placeholder import placeholder

logger = __import__('logging').getLogger(__name__)


EXTENSION_MAP = {
    "gif": {
        "format": "gif",
        "mime_type": "image/gif"
    },
    "jpg": {
        "format": "jpeg",
        "mime_type": "image/jpeg"
    },
    "png": {
        "format": "png",
        "mime_type": "image/png"
    },
}


@cache_control(max_age=settings.BETTY_CACHE_IMAGEJS_SEC)
def image_js(request):
    widths = set(settings.BETTY_WIDTHS + settings.BETTY_CLIENT_ONLY_WIDTHS)
    # Ensure '0' always present
    widths.add(0)

    betty_image_url = settings.BETTY_IMAGE_URL
    # make the url protocol-relative
    url_parts = list(urllib.parse.urlparse(betty_image_url))
    url_parts[0] = ""
    if settings.BETTY_IMAGE_URL_USE_REQUEST_HOST:
        # Prefer requested host (allows serving against multiple domains).
        # Make sure settings.ALLOWED_HOSTS is set to avoid spoofing.
        url_parts[1] = request.get_host()
    betty_image_url = urllib.parse.urlunparse(url_parts)
    if betty_image_url.endswith("/"):
        betty_image_url = betty_image_url[:-1]
    context = {
        "BETTY_IMAGE_URL": betty_image_url,
        "BETTY_WIDTHS": sorted(widths),
        "BETTY_MAX_WIDTH": settings.BETTY_MAX_WIDTH
    }
    BETTY_RATIOS = []
    ratios_sorted = sorted(settings.BETTY_RATIOS,
                           key=lambda r: Ratio(r).width / float(Ratio(r).height))
    for ratio_string in ratios_sorted:
        ratio = Ratio(ratio_string)
        BETTY_RATIOS.append((ratio_string, ratio.width / float(ratio.height)))
    context["BETTY_RATIOS"] = json.dumps(BETTY_RATIOS)

    return render(request, "image.js", context, content_type="application/javascript")


@cache_control(max_age=(60 * 60))
def redirect_crop(request, id, ratio_slug, width, extension):
    image_id = int(id.replace("/", ""))

    """
    This is a little bit of a hack, but basically, we just make a disposable image object,
    so that we can use it to generate a full URL.
    """
    image = Image(id=image_id)

    return HttpResponseRedirect(image.get_absolute_url(ratio=ratio_slug, width=width,
                                                       extension=extension))


def _image_response(image_blob, extension):
    resp = HttpResponse(image_blob)
    resp["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
    resp['Last-Modified'] = http_date()
    return resp


def crop(request, id, ratio_slug, width, extension):
    if ratio_slug != "original" and ratio_slug not in settings.BETTY_RATIOS:
        raise Http404

    try:
        ratio = Ratio(ratio_slug)
    except ValueError:
        raise Http404

    width = int(width)

    if width > settings.BETTY_MAX_WIDTH:
        return HttpResponseServerError("Invalid width")

    image_id = int(id.replace("/", ""))

    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        if settings.BETTY_PLACEHOLDER:
            img_blob = placeholder(ratio, width, extension)
            resp = HttpResponse(img_blob)
            resp["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp["Pragma"] = "no-cache"
            resp["Expires"] = "0"
            resp["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
            return resp
        else:
            raise Http404

    if check_not_modified(request=request, last_modified=image.last_modified):
        # Avoid hitting storage backend on cache update
        resp = HttpResponseNotModified()
    else:
        try:
            image_blob = image.crop(ratio, width, extension)
        except Exception:
            logger.exception("Cropping error")
            return HttpResponseServerError("Cropping error")

        resp = _image_response(image_blob, extension=extension)

    # Optionally specify alternate cache duration for non-breakpoint widths.
    # This is useful b/c cache flush callback only receives paths for known breakpoints, so this
    # allows non-standard widths to have a shorter cache time. This wouldn't be necessary if cache
    # flush used wildcards instead, or if you could guarantee/force only defined breakpoint widths.
    max_age = settings.BETTY_CACHE_CROP_SEC
    if settings.BETTY_CACHE_CROP_NON_BREAKPOINT_SEC is not None:
        if width not in (settings.BETTY_WIDTHS + settings.BETTY_CLIENT_ONLY_WIDTHS):
            max_age = settings.BETTY_CACHE_CROP_NON_BREAKPOINT_SEC
    patch_cache_control(resp, max_age=max_age)
    return resp


# Legacy behavior -- originally these were just dropped on filesystem and let NGINX frontend serve
# automatically via try-files.
def animated(request, id, extension):

    image_id = int(id.replace("/", ""))

    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        raise Http404

    if not image.animated:
        raise Http404

    if check_not_modified(request=request, last_modified=image.last_modified):
        # Avoid hitting storage backend on cache update
        resp = HttpResponseNotModified()
    else:
        try:
            image_blob = image.get_animated(extension=extension)
        except Exception:
            logger.exception("Animated error")
            return HttpResponseServerError("Animated error")

        resp = _image_response(image_blob, extension=extension)

    patch_cache_control(resp, max_age=settings.BETTY_CACHE_CROP_SEC)
    return resp
