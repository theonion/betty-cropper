import os
import random
import copy
import shutil

from betty import app
from betty.database import db_session
from betty.models import Image as ImageObj
from betty.models import Ratio
from betty.crossdomain import crossdomain

from flask import abort, make_response, redirect, jsonify, request, current_app
from werkzeug import secure_filename
from wand.image import Image
from wand.color import Color
from wand.drawing import Drawing

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


@app.route('/<path:id>/<string:ratio_slug>/<int:width>.<string:extension>', methods=['GET'])
def crop(id, ratio_slug, width, extension):
    try:
        ratio = Ratio(ratio_slug)
    except ValueError:
        abort(404)

    if extension not in ('jpg', 'png'):
        abort(404)

    if len(id) > 4 and id == id.replace("/", ""):
        image_id = id.replace("/", "")
        id_string = ""
        for index,char in enumerate(image_id):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        return redirect("%s/%s/%s.%s" % (id_string, ratio_slug, width, extension))

    try:
        image_id = int(id.replace("/", ""))
    except ValueError:
        abort(404)

    image = ImageObj.query.get(image_id)
    if image is None:
        if current_app.config['BETTY'].get('PLACEHOLDER', False):
            return placeholder(ratio, width, extension)
        else:
            abort(404)

    try:
        source_file = open(os.path.join(image.path(), 'src'), 'r')
    except IOError:
        if current_app.config['BETTY'].get('PLACEHOLDER', False):
            return placeholder(ratio, width, extension)
        else:
            abort(404)

    with Image(file=source_file) as img:
        if ratio_slug == 'original':
            ratio.width = img.size[0]
            ratio.height = img.size[1]

        selection = image.get_selection(ratio)

        img.crop(selection['x0'], selection['y0'], selection['x1'], selection['y1'])
        img.transform(resize='%dx' % width)

        if extension == 'jpg':
            img.format = 'jpeg'
            img.compression_quality = 80
        if extension == 'png':
            img.format = 'png'

        img_blob = img.make_blob()

        ratio_dir = os.path.join(os.path.dirname(image.path()), ratio.string)
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
        draw.font = app.config['BETTY']['PLACEHOLDER_FONT']
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
                if extension == 'jpg':
                   resp.headers["Content-Type"] = "image/jpeg"
                if extension == 'png':
                    resp.headers["Content-Type"] = "image/png"
                return resp

@crossdomain('*')
@app.route('/api/new', methods=['POST', 'OPTIONS'])
def new():
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['BETTY']['API_KEY']:
        abort(403)
    
    if 'image' not in request.files:
        abort(400)
    
    image_file = request.files['image']
    with Image(file=image_file) as img:
        width = img.size[0]
        height = img.size[0]

    filename = secure_filename(image_file.filename)
    
    image = ImageObj(name=filename, width=width, height=height, selections={})
    db_session.add(image)
    db_session.commit()

    os.makedirs(image.path())
    image_file.save(os.path.join(image.path(), filename))
    os.symlink(filename, os.path.join(image.path(), 'src'))

    return jsonify(image.to_dict())

@crossdomain('*')
@app.route('/api/<int:id>/<string:ratio>', methods=['POST', 'OPTIONS'])
def update_selection(id, ratio):
    # TODO: move this to a decorator or similar
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['BETTY']['API_KEY']:
        abort(403)

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

    if ratio not in current_app.config['BETTY']['RATIOS']:
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
    
@crossdomain('*')
@app.route('/api/search', methods=['GET', 'OPTIONS'])
def search():
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['BETTY']['API_KEY']:
        abort(403)

    query = request.args.get('q')

    if query:
        q = db_session.query(ImageObj).filter(ImageObj.name.ilike('%' + query + '%')).order_by('-id').limit(25)
    else:
        q = db_session.query(ImageObj).query.order_by('-id').limit(25)
    results = []

    for instance in q:
        results.append(instance.to_dict())
    return jsonify({'results': results})

@crossdomain('*')
@app.route('/api/<int:id>', methods=['GET', 'OPTIONS', 'PATCH'])
def image_detail(id):
    if not app.config['DEBUG'] and request.headers.get('X-Betty-Api-Key') != app.config['BETTY']['API_KEY']:
        abort(403)

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

    return jsonify(image.to_dict())
