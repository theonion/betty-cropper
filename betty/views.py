from .conf.app import settings

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render

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

SIZE_MAP = {
    "large": {
        "width__gte": 1024,
    },
    "medium": {
        "width__gte": 400,
        "width__lt": 1024
    },
    "small": {
        "width__lt": 400
    }
}


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


@login_required
def index(request):
    queryset = Image.objects.all()
    if request.GET.get("size", "all") in SIZE_MAP:
        queryset = queryset.filter(**SIZE_MAP[request.GET["size"]])
    if request.GET.get("q", "") != "":
        queryset = queryset.filter(name__icontains=request.GET.get("q"))

    paginator = Paginator(queryset, 48)
    page = request.GET.get('page')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        images = paginator.page(1)
    except EmptyPage:
        images = paginator.page(paginator.num_pages)

    context = {
        "images": images,
        "q": request.GET.get("q")
    }
    return render(request, "index.html", context)


def upload(request):
    return render(request, "upload.html", {})
