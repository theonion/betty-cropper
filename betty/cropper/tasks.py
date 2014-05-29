from __future__ import absolute_import

import itertools
import os
import tempfile

from celery import shared_task
from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.conf.app import settings


@shared_task()
def optimize_image(image_id):
    from betty.cropper.models import Image, optimized_upload_to

    image = Image.objects.get(id=image_id)

    im = PILImage.open(image.source.path)
    
    # Let's cache some important stuff
    format = im.format
    icc_profile = im.info.get("icc_profile")
    quantization = getattr(im, "quantization", None)
    subsampling = None
    if format == "JPEG":
        subsampling = JpegImagePlugin.get_sampling(im)

    filename = os.path.split(image.source.path)[1]

    if im.size[0] > settings.BETTY_MAX_WIDTH:
        # If the image is really large, we'll save a more reasonable version as the "original"
        height = settings.BETTY_MAX_WIDTH * float(im.size[1]) / float(im.size[0])
        im = im.resize((settings.BETTY_MAX_WIDTH, int(round(height))), PILImage.ANTIALIAS)

        """OK, so this suuuuuucks. When we convert or resize an Image, it
        is no longer a JPEG. So, in order to reset the quanitzation, etc,
        we need to save this to a file and then re-read it from the
        filesystem. Silly, I know. Once my pull request is approved, this
        can be removed, and we can just pass the qtables into the save method.
        PR is here: https://github.com/python-imaging/Pillow/pull/677
        """
        temp = tempfile.NamedTemporaryFile()
        im.save(temp, format="JPEG")
        temp.seek(0)
        im = PILImage.open(temp)

        im.quantization = quantization

    image.optimized.name = optimized_upload_to(image, filename)
    if format == "JPEG":
        # For JPEG files, we need to make sure that we keep the quantization profile
        try:
            im.save(
                image.optimized.name,
                icc_profile=icc_profile,
                quality="keep",
                subsampling=subsampling
            )
        except TypeError as e:
            # Maybe the image already had an invalid quant table?
            if e.message.startswith("Not a valid numbers of quantization tables"):
                im.save(
                    image.optimized.name,
                    icc_profile=icc_profile
                )
            else:
                raise
    else:
        im.save(image.optimized.name, icc_profile=icc_profile)
    image.save()

    return image_id


@shared_task
def search_image_quality(image_id):

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

    def is_optimized(image):
        """Checks if the image is already optimized

        For our purposes, we check to see if the existing file will be smaller than
        a version saved at the default quality (80)."""

        im = PILImage.open(image.source.path)
        icc_profile = im.info.get("icc_profile")

        # First, let's check to make sure that this image isn't already an optimized JPEG
        if im.format == "JPEG":
            optimized_path = tempfile.mkstemp()[1]
            im.save(
                optimized_path,
                format="JPEG",
                quality=settings.BETTY_DEFAULT_JPEG_QUALITY,
                icc_profile=icc_profile,
                optimize=True)
            if os.stat(image.source.path).st_size < os.stat(optimized_path).st_size:
                # Looks like the original was already compressed, let's bail.
                return True
        
        return False

    image = Image.objects.get(id=image_id)
    
    if is_optimized(image):
        return

    im = PILImage.open(image.optimized.path)
    search_im = im.copy()

    area = search_im.size[0] * search_im.size[1]
    max_area = (1000.0 * 1000.0)
    if area > max_area:
        scale = max_area / area
        new_size = (search_im.size[0] * scale, search_im.size[1] * scale)
        search_im = search_im.resize(map(int, new_size), PILImage.ANTIALIAS)
    if search_im.mode != "RGB":
        search_im = search_im.convert("RGB", palette=PILImage.ADAPTIVE)

    original_density = get_color_density(search_im)
    icc_profile = im.info.get("icc_profile")

    search_range = settings.BETTY_JPEG_QUALITY_RANGE

    while (search_range[1] - search_range[0]) > 1:
        quality = int(round(search_range[0] + (search_range[1] - search_range[0]) / 2.0))

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
