from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render

from betty.cropper.models import Image


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


@login_required
def search(request):
    queryset = Image.objects.all().order_by('-id')
    if request.GET.get("size", "all") in SIZE_MAP:
        queryset = queryset.filter(**SIZE_MAP[request.GET["size"]])
    if request.GET.get("q", "") != "":
        queryset = queryset.filter(name__icontains=request.GET.get("q"))

    paginator = Paginator(queryset, 24)
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


@login_required
def upload(request):
    return render(request, "upload.html", {})


@login_required
def crop(request):
    height = 100
    ratios = [
        {
            "name": "3x1",
            "width": 3 * height / 1,
            "height": height
        },
        {
            "name": "2x1",
            "width": 2 * height / 1,
            "height": height
        },
        {
            "name": "16x9",
            "width": 16 * height / 9,
            "height": height
        },
        {
            "name": "4x3",
            "width": 4 * height / 3,
            "height": height
        },
        {
            "name": "1x1",
            "width": 1 * height / 1,
            "height": height
        },
        {
            "name": "3x4",
            "width": 3 * height / 4,
            "height": height
        },
    ]
    return render(request, "crop.html", {"ratios": ratios})
