import random

from .conf.app import settings

from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image as WandImage

from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Image, Ratio

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

BACKGROUND_COLORS = (
    "rgb(153,153,51)",
    "rgb(102,153,51)",
    "rgb(51,153,51)",
    "rgb(153,51,51)",
    "rgb(194,133,71)",
    "rgb(51,153,102)",
    "rgb(153,51,102)",
    "rgb(71,133,194)",
    "rgb(51,153,153)",
    "rgb(153,51,153)",
)

RATIOS = ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9")


def placeholder(ratio, width, extension):
    if ratio.string == "original":
        ratio = Ratio(random.choice((RATIOS)))
    height = (width * ratio.height / float(ratio.width))
    with Drawing() as draw:
        draw.font_size = 52
        draw.gravity = "center"
        draw.fill_color = Color("white")
        with Color(random.choice(BACKGROUND_COLORS)) as bg:
            with WandImage(width=width, height=int(height), background=bg) as img:
                draw.text(0, 0, ratio.string)
                draw(img)

                if extension == 'jpg':
                    img.format = 'jpeg'
                if extension == 'png':
                    img.format = 'png'

                return img.make_blob()


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

    if len(id) > 4 and "/" not in id:
        id_string = ""
        for index, char in enumerate(id):
            if index % 4 == 0 and index != 0:
                id_string += "/"
            id_string += char

        redirect_url = reverse(
            'betty.views.crop',
            args=(id_string, ratio_slug, width, extension)
        )
        return HttpResponseRedirect(redirect_url)

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
        return HttpResponseServerError()

    resp = HttpResponse(image_blob)
    resp["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
    return resp
