from __future__ import absolute_import

import os
import copy
import shutil
from datetime import timedelta
from functools import update_wrapper

from betty.flask import app
from betty.flask.database import db_session
from betty.flask.models import Image as ImageObj
from betty.core import EXTENSION_MAP, Ratio, placeholder

from flask import abort, redirect, jsonify, request, current_app, render_template, make_response
from werkzeug import secure_filename
from wand.image import Image

from slimit import minify

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            else:
                h['Access-Control-Allow-Headers'] = "X-Betty-Api-Key, Content-Type"
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.errorhandler(404)
def page_not_found(e):
    return 'Not found', 404, {"Cache-Control": "max-age=60"}


@app.route('/image.js')
def image_js():
    response = make_response(minify(render_template('image.js.j2', **current_app.config), mangle=True, mangle_toplevel=True))
    response.headers['Content-Type'] = "application/javascript"
    response.headers['Cache-Control'] = "max-age=60"
    return response

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@crossdomain(origin='*')
@app.route('/<path:id>/<string:ratio_slug>/<int:width>.<string:extension>', methods=['GET'])
def crop(id, ratio_slug, width, extension):
    if ratio_slug != "original" and ratio_slug not in current_app.config["RATIOS"]:
        abort(404)

    try:
        ratio = Ratio(ratio_slug)
    except ValueError:
        abort(404)

    if extension not in ('jpg', 'png'):
        abort(404)

    if width > 2000:
        abort(500)

    if len(id) > 4 and id == id.replace("/", ""):
        image_id = id.replace("/", "")
        id_string = ""
        for index,char in enumerate(image_id):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        return redirect("%s%s/%s/%s.%s" % (current_app.config['PUBLIC_URL'], id_string, ratio_slug, width, extension))

    try:
        image_id = int(id.replace("/", ""))
    except ValueError:
        abort(404)

    image = ImageObj.query.get(image_id)
    if image is None:
        if current_app.config.get('PLACEHOLDER', False):
            img_blob = placeholder(ratio, width, extension)

            resp = make_response(img_blob, 200)
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            resp.headers["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
            return resp
        else:
            abort(404)

    try:
        image_blob = image.crop(ratio, width, extension)
    except Exception:
        abort(500)

    resp = make_response(image_blob, 200)
    resp.headers["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
    return resp


@app.route('/api/new', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def new():
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['API_KEY']:
        response = jsonify({'message': 'Not authorized'})
        response.status_code = 403
        return response

    if 'image' not in request.files:
        abort(400)
    
    image_file = request.files['image']
    with Image(file=image_file) as img:
        width = img.size[0]
        height = img.size[1]

        filename = secure_filename(image_file.filename)
        
        image = ImageObj(name=filename, width=width, height=height, selections={})
        db_session.add(image)
        db_session.commit()

        os.makedirs(image.path())
        img.save(filename=os.path.join(image.path(), filename))
        os.symlink(filename, image.src_path())

    return jsonify(image.to_native())

@app.route('/api/<int:id>/<string:ratio>', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
def update_selection(id, ratio):
    # TODO: move this to a decorator or similar
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['API_KEY']:
        response = jsonify({'message': 'Not authorized'})
        response.status_code = 403
        return response

    image = ImageObj.query.get(id)
    if image is None:
        response = jsonify({'message': 'No such image!', 'error': True})
        response.status_code = 404
        return response

    if request.json:
        try:
            selection = {
                'x0': int(request.json['x0']),
                'y0': int(request.json['y0']),
                'x1': int(request.json['x1']),
                'y1': int(request.json['y1']),
            }
        except (KeyError, ValueError):
            response = jsonify({'message': 'Bad selection', 'error': True})
            response.status_code = 400
            return response
    else:
        response = jsonify({'message': 'No selection', 'error': True})
        response.status_code = 400
        return response

    selections = copy.copy(image.selections)
    if selections is None:
        selections = {}

    if ratio not in current_app.config['RATIOS']:
        response = jsonify({'message': 'No such ratio', 'error': True})
        response.status_code = 400
        return response

    selections[ratio] = selection
    image.selections = selections
    db_session.add(image)
    db_session.commit()

    ratio_path = os.path.join(image.path(), ratio)
    if os.path.exists(ratio_path):
        crops = os.listdir(ratio_path)
        # TODO: flush cache on crops
        shutil.rmtree(ratio_path)

    return jsonify({'message': 'OK', 'error': False})
    
@app.route('/api/search', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def search():
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['API_KEY']:
        response = jsonify({'message': 'Not authorized'})
        response.status_code = 403
        return response

    query = request.args.get('q')

    if query:
        q = db_session.query(ImageObj).filter(ImageObj.name.ilike('%' + query + '%')).order_by('-id').limit(25)
    else:
        q = db_session.query(ImageObj).order_by('-id').limit(25)
    results = []

    for instance in q:
        results.append(instance.to_native())
    return jsonify({'results': results})

@app.route('/api/<int:id>', methods=['GET', 'OPTIONS', 'PATCH'])
@crossdomain(origin='*')
def image_detail(id):
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['API_KEY']:
        response = jsonify({'message': 'Not authorized'})
        response.status_code = 403
        return response

    image = ImageObj.query.get(id)
    if image is None:
        abort(404)

    if request.method == 'PATCH':
        if request.json:
            if 'name' in request.json:
                image.name = request.json['name']
            if 'credit' in request.json:
                image.credit = request.json['credit']
            db_session.add(image)
            db_session.commit()
        else:
            response = jsonify({'message': 'No data', 'error': True})
            response.status_code = 400
            return response

    return jsonify(image.to_native())
