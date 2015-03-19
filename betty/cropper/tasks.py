from __future__ import absolute_import

import os
import tempfile

from celery import shared_task
from PIL import Image as PILImage

from betty.conf.app import settings

from .dssim import detect_optimal_quality
try:
    import numpy
    import scipy
    IMGMIN_DISABLED = False
except ImportError:
    IMGMIN_DISABLED = True


def is_optimized(image):
    """Checks if the image is already optimized

    For our purposes, we check to see if the existing file will be smaller than
    a version saved at the default quality (80)."""

    im = PILImage.open(image.source.path)
    icc_profile = im.info.get("icc_profile")

    # First, let's check to make sure that this image isn't already an optimized JPEG
    if im.format == "JPEG":
        fd, optimized_path = tempfile.mkstemp()
        im.save(
            optimized_path,
            format="JPEG",
            quality=settings.BETTY_DEFAULT_JPEG_QUALITY,
            icc_profile=icc_profile,
            optimize=True)
        os.close(fd)
        if os.stat(image.source.path).st_size < os.stat(optimized_path).st_size:
            # Looks like the original was already compressed, let's bail.
            return True

    return False


@shared_task
def search_image_quality(image_id):
    if IMGMIN_DISABLED:
        return

    from betty.cropper.models import Image

    image = Image.objects.get(id=image_id)

    if is_optimized(image):
        # If the image is already optimized, let's leave this alone...
        return

    image.jpeg_quality_settings = {}
    last_width = 0
    for width in sorted(settings.BETTY_WIDTHS, reverse=True):

        if abs(last_width - width) < 100:
            # Sometimes the widths are really too close. We only need to check every 100 px
            continue

        if width > 0:
            quality = detect_optimal_quality(image.optimized.path, width)
            image.jpeg_quality_settings[width] = quality

            if quality == settings.BETTY_JPEG_QUALITY_RANGE[-1]:
                # We'are already at max...
                break

        last_width = width

    image.clear_crops()
    image.save()
