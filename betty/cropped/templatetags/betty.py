from __future__ import absolute_import

from django import template
from django.template.loader import select_template

from betty.cropped.fields import ImageFieldFile, default_storage

register = template.Library()


class AnonymousImageField(object):

    def __init__(self, id):
        self.id = id
        self.storage = default_storage

    def get_crop_url(self, ratio="original", width=600, format="jpg"):
        return self.storage.url(self.id, ratio=ratio, width=width, format=format)


@register.simple_tag
def cropped_url(image, ratio="original", width=600, format="jpg"):
    if not isinstance(image, ImageFieldFile):
        try:
            image_id = int(image)
        except:
            raise
            raise template.TemplateSyntaxError("\"{}\" is not a valid ImageField or image id".format(image))
        image = AnonymousImageField(image_id)

    return image.get_crop_url(ratio=ratio, width=width, format=format)


@register.simple_tag
def cropped(image, ratio="original", width=600, format="jpg"):
    if not isinstance(image, ImageFieldFile):
        try:
            image_id = int(image)
        except:
            raise
            raise template.TemplateSyntaxError("\"{}\" is not a valid ImageField or image id".format(image))
        image = AnonymousImageField(image_id)

    t = select_template(["betty/cropped.html", "betty/cropped_default.html"])
    context = template.Context({
        "image": image,
        "image_url": image.get_crop_url(ratio=ratio, width=width, format=format),
        "ratio": ratio,
        "width": width,
        "format": format
    })
    return t.render(context)
