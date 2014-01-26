from .conf import settings

from betty.core import EXTENSION_MAP, Ratio, placeholder

from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Image

def crop(request, id, ratio_slug, width, extension):
    if ratio_slug != "original" and ratio_slug not in settings.BETTY_CROPPER["RATIOS"]:
        raise Http404

    try:
        ratio = Ratio(ratio_slug)
    except ValueError:
        raise Http404

    try:
        width = int(width)
    except ValueError:
        return HttpResponseServerError()

    if width > 2000:
        return HttpResponseServerError()

    if len(id) > 4 and "/" not in id:
        id_string = ""
        for index,char in enumerate(id):
            if index % 4 == 0 and index != 0:
                id_string += "/"
            id_string += char

        return HttpResponseRedirect(reverse('betty.djbetty.views.crop', args=(id_string, ratio_slug, width, extension)))

    try:
        image_id = int(id.replace("/", ""))
    except ValueError:
        raise Http404

    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        if settings.BETTY_CROPPER["PLACEHOLDER"]:
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
        return HttpResponseServerError()

    resp = HttpResponse(image_blob)
    resp["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
    return resp
