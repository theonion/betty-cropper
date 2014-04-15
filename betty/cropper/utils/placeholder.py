import io
import random

from PIL import Image, ImageDraw, ImageFont

from betty.cropper.models import Ratio
from betty.conf.app import settings


def placeholder(ratio, width, extension):
    if ratio.string == "original":
        ratio = Ratio(random.choice((settings.BETTY_RATIOS)))
    height = int(round((width * ratio.height / float(ratio.width))))

    bg_fill = random.choice(settings.BETTY_PLACEHOLDER_COLORS)
    img = Image.new("RGB", (width, height), bg_fill)

    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(filename=settings.BETTY_PLACEHOLDER_FONT, size=45)
    text_size = draw.textsize(ratio.string, font=font)
    text_coords = (
        int(round((width - text_size[0]) / 2.0)),
        int(round((height - text_size[1]) / 2) - 15),
    )
    draw.text(text_coords, ratio.string, font=font, fill=(256, 256, 256))
    if extension == 'jpg':
        pillow_kwargs = {"format": "jpeg", "quality": 80}
    if extension == 'png':
        pillow_kwargs = {"format": "png"}

    tmp = io.BytesIO()
    img.save(tmp, **pillow_kwargs)
    return tmp.getvalue()
