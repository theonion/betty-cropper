import io
import random

from PIL import Image, ImageDraw, ImageFont

from betty.cropper.models import Ratio
from betty.conf.app import settings


def placeholder(ratio, width, extension):
    if ratio.string == "original":
        ratio = Ratio(random.choice((settings.BETTY_RATIOS)))
    height = int(round((width * ratio.height / float(ratio.width))))

    img = Image.new("RGB", (width, height))

    draw = ImageDraw.Draw(img)
    bg_fill = random.choice(settings.BETTY_PLACEHOLDER_COLORS)
    draw.rectangle((0, 0, width, height), fill=bg_fill)

    print(settings.BETTY_PLACEHOLDER_FONT)
    font = ImageFont.truetype(filename=settings.BETTY_PLACEHOLDER_FONT, size=45)
    text_size = draw.textsize(ratio.string, font=font)
    text_coords = (
        int(round((width / 2.0) - (text_size[0] / 2.0))),
        int(round((height / 2.0) - (text_size[1] / 2.0))),
    )
    draw.text(text_coords, ratio.string, font=font)
    if extension == 'jpg':
        pillow_kwargs = {"format": "jpeg", "quality": 80}
    if extension == 'png':
        pillow_kwargs = {"format": "png"}

    tmp = io.BytesIO()
    img.save(tmp, **pillow_kwargs)
    return tmp.getvalue()
