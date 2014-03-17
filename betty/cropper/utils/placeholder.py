import random

from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

from betty.cropper.models import Ratio
from betty.conf.app import settings


def placeholder(ratio, width, extension):
    if ratio.string == "original":
        ratio = Ratio(random.choice((settings.BETTY_RATIOS)))
    height = (width * ratio.height / float(ratio.width))
    with Drawing() as draw:
        draw.font_size = 52
        draw.gravity = "center"
        draw.fill_color = Color("white")
        with Color(random.choice(settings.BETTY_PLACEHOLDER_COLORS)) as bg:
            with Image(width=width, height=int(height), background=bg) as img:
                draw.text(0, 0, ratio.string)
                draw(img)

                if extension == 'jpg':
                    img.format = 'jpeg'
                if extension == 'png':
                    img.format = 'png'

                return img.make_blob()
