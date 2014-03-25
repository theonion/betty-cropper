from betty.conf.app import settings

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
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
def redirect_crop(request, id, ratio_slug, width, extension):
    id_string = ""
    for index, char in enumerate(id):
        if index % 4 == 0 and index != 0:
            id_string += "/"
        id_string += char

    redirect_url = reverse(
        'betty.cropper.views.crop',
        args=(id_string, ratio_slug, width, extension)
    )
    return HttpResponseRedirect(redirect_url)


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
