## Betty Cropper (Flask Edition)

[![Build Status](https://travis-ci.org/theonion/betty-cropper.png?branch=master)](https://travis-ci.org/theonion/betty-cropper)
[![Coverage Status](https://coveralls.io/repos/theonion/betty-cropper/badge.png)](https://coveralls.io/r/theonion/betty-cropper)

### Get started:

    > pip install -r requirements.txt
    > cp settings.py.example settings.py  # Edit values as necessary.
    > python runserver.py

### API

__POST__ an image (using the key "image") to /api/new, for example:
    
    > curl --form "image=@Lenna.png" http://localhost:5000/api/new

This should return an image id ("1", if this is the first image).

You can get a cropped version of this image using a URL like: [http://localhost:5000/1/1x1/300.jpg](http://localhost:5000/1/1x1/300.jpg).

To get the data form an image, send a GET request to /api/id, for example:

    > curl http://localhost:5000/api/1

To update the name or credit, use a PATCH on that same endpoint:

    > curl -XPATCH -H "Content-Type: application/json" -d '{"name":"Testing", "credit":"Some guy"}' http://localhost:5000/api/1

To update the selections used for a crop, you can POST to /api/id/ratio, for example:

    > curl -X POST -H "Content-Type: application/json" -d '{"x0":1,"y0":1,"x1":510,"y1":510}' http://localhost:5000/api/1/1x1

__GET__ /api/search, with an option "q" parameter in order to get a list of files matching that description. For example:

    > curl -XGET http://localhost:5000/api/search?q=lenna

### TODOs

- ES integration?
- Put credit on the image itself?
- Add nginx/uwsgi instructions
- Build embedded uwsgi binary, package with fpm?
