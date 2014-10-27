import json
from betty.conf.app import settings

from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from six.moves import urllib

from .models import Image, Ratio
from .utils.placeholder import placeholder

EXTENSION_MAP = {
    "jpg": {
        "format": "jpeg",
        "mime_type": "image/jpeg"
    },
    "png": {
        "format": "png",
        "mime_type": "image/png"
    },
}


@cache_control(max_age=300)
def image_js(request):
    widths = settings.BETTY_WIDTHS
    if 0 not in widths:
        widths.append(0)

    betty_image_url = settings.BETTY_IMAGE_URL
    # make the url protocol-relative
    url_parts = list(urllib.parse.urlparse(betty_image_url))
    url_parts[0] = ""
    betty_image_url = urllib.parse.urlunparse(url_parts)
    if betty_image_url.endswith("/"):
        betty_image_url = betty_image_url[:-1]
    context = {
        "BETTY_IMAGE_URL": betty_image_url,
        "BETTY_WIDTHS": sorted(widths),
        "BETTY_MAX_WIDTH": settings.BETTY_MAX_WIDTH
    }
    BETTY_RATIOS = []
    ratios_sorted = sorted(settings.BETTY_RATIOS, key=lambda r: Ratio(r).width / float(Ratio(r).height))
    for ratio_string in ratios_sorted:
        ratio = Ratio(ratio_string)
        BETTY_RATIOS.append((ratio_string, ratio.width / float(ratio.height)))
    context["BETTY_RATIOS"] = json.dumps(BETTY_RATIOS)

    return render(request, "image.js", context, content_type="application/javascript")


@cache_control(max_age=300)
def redirect_crop(request, id, ratio_slug, width, extension):
    image_id = int(id.replace("/", ""))

    """
    This is a little bit of a hack, but basically, we just make a disposable image object,
    so that we can use it to generate a full URL.
    """
    image = Image(id=image_id)

    return HttpResponseRedirect(image.get_absolute_url(ratio=ratio_slug, width=width, format=extension))


@cache_control(max_age=300)
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

    try:
        image_blob = image.crop(ratio, width, extension)
    except Exception:
        return HttpResponseServerError("Cropping error")

    resp = HttpResponse(image_blob)
    resp["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
    return resp
