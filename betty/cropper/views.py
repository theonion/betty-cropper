import json
from betty.conf.app import settings

from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import cache_control

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
    context = {
        "BETTY_IMAGE_URL": settings.BETTY_IMAGE_URL,
        "BETTY_WIDTHS": settings.BETTY_WIDTHS,
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
    try:
        image_id = int(id.replace("/", ""))
    except ValueError:
        raise Http404

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

    try:
        width = int(width)
    except ValueError:
        return HttpResponseServerError("Invalid width")

    if width > 2000:
        return HttpResponseServerError("Invalid width")

    try:
        image_id = int(id.replace("/", ""))
    except ValueError:
        raise Http404

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
