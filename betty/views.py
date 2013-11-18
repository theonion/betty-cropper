import os
import random
from betty import app
from betty.database import db_session
from betty.models import Image as ImageObj
from betty.models import Ratio

from flask import abort, make_response, redirect, jsonify
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


@app.route('/<path:id>/<string:ratio_slug>/<int:width>.<string:extension>')
def crop(id, ratio_slug, width, extension):
    try:
        ratio = Ratio(ratio_slug)
    except ValueError:
        abort(404)

    if extension not in ('jpg', 'png'):
        abort(404)

    if width > 2000:
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
        if app.config['BETTY'].get('PLACEHOLDER', False):
            return placeholder(ratio, width, extension)
        else:
            abort(404)

    try:
        source_file = open(image.path(), 'r')
    except IOError:
        if app.config['BETTY'].get('PLACEHOLDER', False):
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

@app.route('/api/<int:id>')
def api_detail(id):
    image = ImageObj.query.get(id)
    if image is None:
        abort(404)

    return jsonify(image.to_dict())

if __name__ == '__main__':
    app.run(debug=True)