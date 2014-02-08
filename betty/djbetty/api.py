import json

from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseNotAuthorized,
    HttpResponseBadRequest
)

from .conf import settings
 
ACC_HEADERS = {'Access-Control-Allow-Origin': '*', 
               'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
               'Access-Control-Max-Age': 1000,
               'Access-Control-Allow-Headers': '*'}
 
def crossdomain(func, origin="*", methods=[], headers=["X-Betty-Api-Key", "Content-Type"]):
    """ Sets Access Control request headers."""
    def wrap(request, *args, **kwargs):
        # Firefox sends 'OPTIONS' request for cross-domain javascript call.
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
    return wrap


@crossdomain(methods=['POST', 'OPTIONS'])
def new(request):
    if not settings.BETTY_CROPPER['DEBUG'] and request.META.get('X_BETTY_API_KEY') != settings.BETTY_CROPPER['API_KEY']:
        return HttpResponseNotAuthorized(json.dumps({'message': 'Not authorized'}), content_type="application/json")

    if 'image' not in request.files:
        return HttpResponseBadRequest()
    
    image = Image.objects.create(name=image_file.filename)
    path = image.set_file(image_file)
    image.source.name = 

    image_file = request.files['image']
    with Image(file=image_file) as img:
        width = img.size[0]
        height = img.size[1]
        
        image = ImageObj(name=filename, width=width, height=height, selections={})
        db_session.add(image)
        db_session.commit()

        os.makedirs(image.path())
        img.save(filename=os.path.join(image.path(), filename))
        os.symlink(filename, image.src_path())

    return jsonify(image.to_native())
