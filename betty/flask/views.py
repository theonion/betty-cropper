from __future__ import absolute_import

import os
import random
import copy
import shutil
from datetime import timedelta
from functools import update_wrapper

from betty.flask import app
from betty.flask.database import db_session
from betty.flask.models import Image as ImageObj
from betty.core import Ratio

from flask import abort, redirect, jsonify, request, current_app, render_template, make_response
from werkzeug import secure_filename
from wand.image import Image
from wand.color import Color
from wand.drawing import Drawing
from slimit import minify

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
            return placeholder(ratio, width, extension)
        else:
            abort(404)

    try:
        source_file = open(image.src_path(), 'r')
    except IOError:
        if current_app.config.get('PLACEHOLDER', False):
            # We don't really know how to render an "original" placeholder, so we'll make it a 4x3
            if ratio_slug == 'original':
                ratio.width = 4
                ratio.height = 3
            return placeholder(ratio, width, extension)
        else:
            abort(404)

    with Image(file=source_file, format=extension) as img:
        if ratio_slug == 'original':
            ratio.width = img.size[0]
            ratio.height = img.size[1]

        selection = image.get_selection(ratio)
        try:
            img.crop(selection['x0'], selection['y0'], selection['x1'], selection['y1'])
        except ValueError:
            # Uhoh, looks like we have bad height and width data. Let's reload that and try again.
            image.width = img.size[0]
            image.height = img.size[1]
            db_session.add(image)
            db_session.commit()

            selection = image.get_selection(ratio)
            img.crop(selection['x0'], selection['y0'], selection['x1'], selection['y1'])

        img.transform(resize='%dx' % width)

        # TODO: do we even want to do image credit this way?
        # if image.credit and width >= app.config.get('CREDIT_SIZE_LIMIT'):
        #     with Drawing() as draw:

        #         draw.font = app.config.get('CREDIT_FONT')
        #         draw.gravity = "south_east"
        #         draw.font_size = 10
        #         metrics = draw.get_font_metrics(img, image.credit, multiline=False)

        #         draw.fill_color = Color("rgba(0, 0, 0, 0.0)")
        #         draw.stroke_color = Color("rgba(0, 0, 0, 0.2)")
        #         draw.stroke_width = metrics.text_height + 10
        #         draw_y = img.size[1] - (metrics.text_height - 5)
        #         draw.line((img.size[0] - metrics.text_width - 10, draw_y), (img.size[0], draw_y))

        #         draw.fill_color = Color("white")
        #         draw.stroke_color = Color("white")
        #         draw.stroke_width = 1.0
        #         draw.text(5, 5, image.credit)
        #         draw(img)

        if extension == 'jpg':
            img.format = 'jpeg'
            img.compression_quality = 80
        if extension == 'png':
            img.format = 'png'

        img_blob = img.make_blob()

        ratio_dir = os.path.join(image.path(), ratio.string)
        try:
            os.makedirs(ratio_dir)
        except OSError as e:
            if e.errno != 17:
                abort(500)

        with open(os.path.join(ratio_dir, "%d.%s" % (width, extension)), 'w+') as out:
            out.write(img_blob)

        resp = make_response(img_blob, 200)
        if extension == 'jpg':
           resp.headers["Content-Type"] = "image/jpeg"
        if extension == 'png':
            resp.headers["Content-Type"] = "image/png"
        return resp
    abort(500)


def placeholder(ratio, width, extension):
    height = (width * ratio.height / float(ratio.width))
    with Drawing() as draw:
        draw.font = os.path.join(os.path.dirname(__file__), "font/OpenSans-Semibold.ttf")
        draw.font_size = 52
        draw.gravity = "center"
        draw.fill_color = Color("white")
        with Color(random.choice(BACKGROUND_COLORS)) as bg:
            with Image(width=width, height=int(height), background=bg) as img:
                draw.text(0, 0, ratio.string)
                draw(img)

                if extension == 'jpg':
                    img.format = 'jpeg'
                if extension == 'png':
                    img.format = 'png'

                img_blob = img.make_blob()

                resp = make_response(img_blob, 200)
                resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                resp.headers["Pragma"] = "no-cache"
                resp.headers["Expires"] = "0"
                if extension == 'jpg':
                   resp.headers["Content-Type"] = "image/jpeg"
                if extension == 'png':
                    resp.headers["Content-Type"] = "image/png"
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
