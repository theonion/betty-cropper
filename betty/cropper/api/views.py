import json
import os
import shutil
import zlib

from django.core.cache import cache
from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseBadRequest,
    HttpResponseNotFound
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from PIL import Image as PILImage
from PIL import ImageFile
from PIL import JpegImagePlugin

from betty.conf.app import settings
from .decorators import betty_token_auth
from betty.cropper.models import Image, source_upload_to, optimized_upload_to
from betty.cropper.tasks import search_image_quality


ACC_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Max-Age': 1000,
    'Access-Control-Allow-Headers': '*'
}


def crossdomain(origin="*", methods=[], headers=["X-Betty-Api-Key", "Content-Type", "X-CSRFToken"]):

    def _method_wrapper(func):

        def _crossdomain_wrapper(request, *args, **kwargs):
            if request.method != "OPTIONS":
                response = func(request, *args, **kwargs)
            else:
                response = HttpResponse()
            response["Access-Control-Allow-Origin"] = "*"
            if methods:
                if request.method not in methods:
                    return HttpResponseNotAllowed(methods)
                response["Access-Control-Allow-Methods"] = ", ".join(methods)
            if headers:
                response["Access-Control-Allow-Headers"] = ", ".join(headers)
            return response

        return _crossdomain_wrapper

    return _method_wrapper


@never_cache
@csrf_exempt
@crossdomain(methods=['POST', 'OPTIONS'])
@betty_token_auth(["server.image_add"])
def new(request):

    image_file = request.FILES.get("image")
    if image_file is None:
        return HttpResponseBadRequest(json.dumps({'message': 'No image'}))
    filename = image_file.name

    image = Image.objects.create(
        name=request.POST.get("name") or filename,
        credit=request.POST.get("credit")
    )
    os.makedirs(image.path())
    source_path = source_upload_to(image, filename)
    original = open(source_path, "wb+")

    parser = ImageFile.Parser()
    try:
        for chunk in image_file.chunks():
            try:
                parser.feed(chunk)
                original.write(chunk)
            except zlib.error as e:
                if e.args[0].startswith("Error -5"):
                    pass
                else:
                    raise
    except:
        pass

    try:
        img = parser.close()
    except IOError:
        return HttpResponseBadRequest(json.dumps({'message': 'Bad image'}))
    original.close()

    # Cache the icc_profile, in case we need to resize this on save.
    icc_profile = img.info.get("icc_profile")
    if img.format == "JPEG":
        quantization = img.quantization
        sampling = JpegImagePlugin.get_sampling(img)

    # If the image is a GIF, we need to do some special stuff
    if img.format == "GIF":
        image.animated = True

        os.makedirs(os.path.join(image.path(), "animated"))

        # First, let's copy the original
        animated_path = os.path.join(image.path(), "animated/original.gif")
        shutil.copy(source_path, animated_path)
        
        # Next, we'll make a thumbnail of the original
        still_path = os.path.join(image.path(), "animated/original.jpg")
        if img.mode != "RGB":
            jpeg = img.convert("RGB")
            jpeg.save(still_path, "JPEG")
        else:
            img.save(still_path, "JPEG")

    elif img.size[0] > settings.BETTY_MAX_WIDTH:
        # If the image is really large, we'll save a more reasonable version as the "original"
        height = settings.BETTY_MAX_WIDTH * float(img.size[1]) / float(img.size[0])
        img = img.resize((settings.BETTY_MAX_WIDTH, int(round(height))), PILImage.ANTIALIAS)
    
    optimized_path = optimized_upload_to(image, filename)
    if img.format == "JPEG":
        # For JPEG files, we need to make sure that we keep the quantization profile
        img.save(
            optimized_path,
            icc_profile=icc_profile,
            quality="keep",
            quantization=quantization,
            subsampling=sampling)
    else:
        img.save(optimized_path, icc_profile=icc_profile)
    
    img.width = img.size[0]
    img.height = img.size[1]
    image.source.name = source_path
    image.optimized.name = optimized_path
    image.save()

    if settings.BETTY_JPEG_QUALITY_RANGE:
        search_image_quality.delay(image.id)

    return HttpResponse(json.dumps(image.to_native()), content_type="application/json")


@never_cache
@csrf_exempt
@crossdomain(methods=['POST', 'OPTIONS'])
@betty_token_auth(["server.image_crop"])
def update_selection(request, image_id, ratio_slug):

    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        message = json.dumps({"message": "No such image!"})
        return HttpResponseNotFound(message, content_type="application/json")

    try:
        request_json = json.loads(request.body.decode("utf-8"))
    except Exception:
        message = json.dumps({"message": "Bad JSON"})
        return HttpResponseBadRequest(message, content_type="application/json")
    try:
        selection = {
            "x0": int(request_json["x0"]),
            "y0": int(request_json["y0"]),
            "x1": int(request_json["x1"]),
            "y1": int(request_json["y1"]),
        }
    except (KeyError, ValueError):
        message = json.dumps({"message": "Bad selection"})
        return HttpResponseBadRequest(message, content_type="application/json")

    if ratio_slug not in settings.BETTY_RATIOS:
        message = json.dumps({"message": "No such ratio"})
        return HttpResponseBadRequest(message, content_type="application/json")

    if image.selections is None:
        image.selections = {}

    image.selections[ratio_slug] = selection
    cache.delete("image-{}".format(image.id))
    image.save()

    ratio_path = os.path.join(image.path(), ratio_slug)
    if os.path.exists(ratio_path):
        if settings.BETTY_CACHE_FLUSHER:
            for crop in os.listdir(ratio_path):
                width, format = crop.split(".")
                ratio = os.path.basename(ratio_path)
                full_url = image.get_absolute_url(ratio=ratio, width=width, format=format)
                settings.BETTY_CACHE_FLUSHER(full_url)
            
        shutil.rmtree(ratio_path)

    return HttpResponse(json.dumps(image.to_native()), content_type="application/json")


@never_cache
@csrf_exempt
@crossdomain(methods=['GET', 'OPTIONS'])
@betty_token_auth(["server.image_read"])
def search(request):

    results = []
    query = request.GET.get("q")
    if query:
        for image in Image.objects.filter(name__icontains=query)[:20]:
            results.append(image.to_native())
    else:
        for image in Image.objects.all()[:20]:
            results.append(image.to_native())

    return HttpResponse(json.dumps({"results": results}), content_type="application/json")


@never_cache
@csrf_exempt
@crossdomain(methods=["GET", "PATCH", "OPTIONS"])
def detail(request, image_id):

    @betty_token_auth(["server.image_change"])
    def patch(request, image_id):

        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            message = json.dumps({"message": "No such image!"})
            return HttpResponseNotFound(message, content_type="application/json")

        try:
            request_json = json.loads(request.body.decode("utf-8"))
        except Exception:
            message = json.dumps({"message": "Bad Request"})
            return HttpResponseBadRequest(message, content_type="application/json")

        for field in ("name", "credit", "selections"):
            if field in request_json:
                setattr(image, field, request_json[field])
        cache.delete("image-{}".format(image.id))
        image.save()

        return HttpResponse(json.dumps(image.to_native()), content_type="application/json")

    @betty_token_auth(["server.image_read"])
    def get(request, image_id):
        cache_key = "image-{}".format(image_id)
        data = cache.get(cache_key)
        if data is None:
            try:
                image = Image.objects.get(id=image_id)
            except Image.DoesNotExist:
                message = json.dumps({"message": "No such image!"})
                return HttpResponseNotFound(message, content_type="application/json")
            data = image.to_native()
            cache.set(cache_key, data, 60 * 60)

        return HttpResponse(json.dumps(data), content_type="application/json")

    if request.method == "PATCH":
        return patch(request, image_id)
    return get(request, image_id)
