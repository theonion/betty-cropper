## Betty Cropper

[![Build Status](https://travis-ci.org/theonion/betty-cropper.svg?branch=master)](https://travis-ci.org/theonion/betty-cropper)
[![Coverage Status](https://coveralls.io/repos/theonion/betty-cropper/badge.png)](https://coveralls.io/r/theonion/betty-cropper)
[![Latest Version](https://pypip.in/version/betty-cropper/badge.svg)](https://pypi.python.org/pypi/betty-cropper/)

### Get started developing:

    > git clone git@github.com:theonion/betty-cropper.git
    > cd betty-cropper
    > virtualenv .
    > source bin/activate
    > pip install -e .
    > pip install file://$(pwd)#egg=betty-cropper[dev]

To run the tests:

    > py.test tests/

### To run an instance of the server

First, make sure that you've installed the development packages for JPEG, PNG, etc.

    > pip install betty-cropper
    > betty-cropper init

Then edit the settings in `betty.conf.py` (if you want to use the dev server, you'll want to set DEBUG=True).

    > betty-cropper syncdb        # Do the intial django sync
    > betty-cropper migrate       # Migrate with south 
    > betty-cropper create_token  # Create an auth token, to use the API
    > betty-cropper runserver

### API

Currently, authentication means sending an `X-Betty-Api-Key` header with a value of your public token. This will likely change to something more mature in future versions.

`POST` an image (using the key "image") to /api/new, for example:
    
    > curl -H "X-Betty-Api_key: YOUR_PUBLIC_TOKEN" --form "image=@Lenna.png" http://localhost:8000/api/new

This should return JSON representing that image and its crops, for instance:

    {
        "name": "Lenna.png",
        "width": 512,
        "selections": {
            "16x9": {"y1": 400, "y0": 112, "x0": 0, "x1": 512, "source": "auto"},
            "3x1": {"y1": 341, "y0": 171, "x0": 0, "x1": 512, "source": "auto"},
            "1x1": {"y1": 512, "y0": 0, "x0": 0, "x1": 512, "source": "auto"},
            "3x4": {"y1": 512, "y0": 0, "x0": 64, "x1": 448, "source": "auto"},
            "2x1": {"y1": 384, "y0": 128, "x0": 0, "x1": 512, "source": "auto"},
            "4x3": {"y1": 448, "y0": 64, "x0": 0, "x1": 512, "source": "auto"}
            },
        "height": 512,
        "credit": null,
        "id": 1
    }

You can get a cropped version of this image using a URL like: [http://localhost:8000/1/1x1/300.jpg](http://localhost:8000/1/1x1/300.jpg).

To get the data form an image, send a `GET` request to /api/id, for example:

    > curl -H "X-Betty-Api_key: YOUR_PUBLIC_TOKEN" http://localhost:8000/api/1

To update the name or credit, use a `PATCH` on that same endpoint:

    > curl -H "X-Betty-Api_key: YOUR_PUBLIC_TOKEN" \
           -H "Content-Type: application/json" \
           -XPATCH http://localhost:8000/api/1 \
           -d '{"name":"Testing", "credit":"Some guy"}'

To update the selections used for a crop, you can `POST` to /api/id/ratio, for example:

    > curl -H "X-Betty-Api_key: YOUR_PUBLIC_TOKEN" \
           -H "Content-Type: application/json" \
           -XPOST http://localhost:8000/api/1/1x1 \
           -d '{"x0":1,"y0":1,"x1":510,"y1":510}' 

`GET` /api/search, with an option "q" parameter in order to get a list of files matching that description. For example:

    > curl -H "X-Betty-Api_key: YOUR_PUBLIC_TOKEN" -XGET http://localhost:8000/api/search?q=lenna
