import json
import io

from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseForbidden,
    HttpResponseBadRequest
)

from .conf import settings
from .models import Image
 
ACC_HEADERS = {'Access-Control-Allow-Origin': '*', 
               'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
               'Access-Control-Max-Age': 1000,
               'Access-Control-Allow-Headers': '*'}


def crossdomain(origin="*", methods=[], headers=["X-Betty-Api-Key", "Content-Type"]):

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


@crossdomain(methods=['POST', 'OPTIONS'])
def new(request):
    if request.META.get("HTTP_X_BETTY_API_KEY") != settings.BETTY_CROPPER["API_KEY"]:
        print("{0} != {1}".format(request.META.get("HTTP_X_BETTY_API_KEY"), settings.BETTY_CROPPER["API_KEY"]))
        return HttpResponseForbidden(json.dumps({'message': 'Not authorized'}), content_type="application/json")        

    image_file = request.FILES.get("image")
    if image_file is None:
        return HttpResponseBadRequest()

    with io.BytesIO() as f:
        for chunk in image_file.chunks():
            f.write(chunk)
        f.seek(0)

        image = Image.objects.create(name=image_file.name)
        path = image.set_file(f)
        image.source.name = path
        image.save()

    return HttpResponse(json(image.to_native()), content_type="application/json")
