from __future__ import absolute_import

import itertools
import os
import tempfile

from celery import shared_task
from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.conf.app import settings
from betty.cropper.models import Image


COLOR_DENSITY_RATIO = 0.11


def get_color_density(im):
    area = im.size[0] * im.size[1]
    unique_colors = len(filter(None, im.histogram()))
    return unique_colors / float(area)


def get_error(a, b):
    assert a.size == b.size
    difference = 0
    for color_sets in itertools.izip(a.getdata(), b.getdata()):
        distance = 0
        for color_pair in zip(color_sets[0], color_sets[1]):
            distance += ((color_pair[0] - color_pair[1]) ** 2)
        difference += (distance ** 0.5)

    pixel_error = difference / float(b.size[0] * b.size[1])
    return pixel_error


@shared_task
def search_image_quality(image_id):

    image = Image.objects.get(id=image_id)
    
    im = PILImage.open(image.optimized.path)
    search_im = im.copy()

    area = search_im.size[0] * search_im.size[1]
    max_area = (1000.0 * 1000.0)
    if area > max_area:
        scale = max_area / area
        new_size = (search_im.size[0] * scale, search_im.size[1] * scale)
        search_im = search_im.resize(map(int, new_size), PILImage.ANTIALIAS)
    if im.mode != "RGB":
        im = im.convert("RGB", palette=PILImage.ADAPTIVE)

    original_density = get_color_density(search_im)
    icc_profile = im.info.get("icc_profile")

    search_range = settings.BETTY_JPEG_QUALITY_RANGE

    # First, let's check to make sure that this image isn't already an optimized JPEG
    if im.format == "JPEG":
        original_path = tempfile.mkstemp()[1]
        search_im.save(
            original_path,
            "JPEG",
            qtables=im.quantization,
            subsampling=JpegImagePlugin.get_sampling(im),
            icc_profile=icc_profile)
        optimized_path = tempfile.mkstemp()[1]
        search_im.save(
            optimized_path,
            "JPEG",
            quality=settings.BETTY_DEFAULT_JPEG_QUALITY,
            icc_profile=icc_profile,
            optimize=True)
        if os.stat(original_path).st_size < os.stat(optimized_path).st_size:
            # Looks like the original was already compressed, let's bail.
            return

    while (search_range[1] - search_range[0]) > 1:
        quality = int(round(search_range[0] + (search_range[1] - search_range[0]) / 2.0))
        print("Searching: {}".format(quality))

        output_filepath = tempfile.mkstemp()[1]
        search_im.save(output_filepath, "jpeg", quality=quality, icc_profile=icc_profile, optimize=True)
        saved = PILImage.open(output_filepath)

        pixel_error = get_error(saved, search_im)
        density_ratio = (get_color_density(saved) - original_density) / original_density

        if pixel_error > settings.BETTY_JPEG_MAX_ERROR or density_ratio > COLOR_DENSITY_RATIO:
            search_range = (quality, search_range[1])
        else:
            search_range = (search_range[0], quality)
        os.remove(output_filepath)

    image.jpeg_quality = search_range[1]
    image.save()
