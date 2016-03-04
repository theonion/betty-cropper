import json

from django.core.cache import cache
from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseBadRequest,
    HttpResponseNotFound
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from betty.conf.app import settings
from .decorators import betty_token_auth
from betty.cropper.models import Image


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

    image = Image.objects.create_from_path(
        image_file.temporary_file_path(),
        filename=image_file.name,
        name=request.POST.get("name"),
        credit=request.POST.get("credit")
    )

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
    cache.delete(image.cache_key())
    image.save()

    image.clear_crops(ratios=[ratio_slug])

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
@crossdomain(methods=["GET", "PATCH", "OPTIONS", "DELETE"])
def detail(request, image_id):

    @betty_token_auth(["server.image_delete"])
    def delete(request, image_id):

        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            message = json.dumps({"message": "No such image!"})
            return HttpResponseNotFound(message, content_type="application/json")

        cache.delete(image.cache_key())
        image.delete()

        return HttpResponse(json.dumps({"message": "OK"}), content_type="application/json")

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
        cache.delete(image.cache_key())
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

    if request.method == "DELETE":
        return delete(request, image_id)
    elif request.method == "PATCH":
        return patch(request, image_id)
    return get(request, image_id)
