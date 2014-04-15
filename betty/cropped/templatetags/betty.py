from django import template
from django.template.loader import select_template

register = template.Library()


@register.simple_tag
def cropped_url(image, ratio="original", width=600, format="jpg"):
    return image.get_crop_url(ratio=ratio, width=width, format=format)


@register.simple_tag
def cropped(image, ratio="original", width=600, format="jpg"):
    t = select_template(["betty/cropped.html", "betty/cropped_default.html"])
    context = template.Context({
        "image": image,
        "image_url": image.get_crop_url(ratio=ratio, width=width, format=format),
        "ratio": ratio,
        "width": width,
        "format": format
    })
    return t.render(context)
