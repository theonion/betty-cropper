from __future__ import absolute_import

import io

from celery import shared_task
from PIL import Image as PILImage

from betty.conf.app import settings

from .dssim import detect_optimal_quality
try:
    # Legacy check: Try import here to determine if we should enable IMGMIN
    import numpy  # NOQA
    import scipy  # NOQA
    IMGMIN_DISABLED = False
except ImportError:
    IMGMIN_DISABLED = True


def is_optimized(image_field):
    """Checks if the image is already optimized

    For our purposes, we check to see if the existing file will be smaller than
    a version saved at the default quality (80)."""

    source_buffer = image_field.read_source_bytes()

    im = PILImage.open(source_buffer)
    icc_profile = im.info.get("icc_profile")

    # First, let's check to make sure that this image isn't already an optimized JPEG
    if im.format == "JPEG":
        optimized_buffer = io.BytesIO()
        im.save(
            optimized_buffer,
            format="JPEG",
            quality=settings.BETTY_DEFAULT_JPEG_QUALITY,
            icc_profile=icc_profile,
            optimize=True)
        # Note: .getbuffer().nbytes is preferred, but not supported in Python 2.7
        if len(source_buffer.getvalue()) < len(optimized_buffer.getvalue()):
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

    # Read buffer from storage once and reset on each iteration
    optimized_buffer = image.read_optimized_bytes()
    image.jpeg_quality_settings = {}
    last_width = 0
    for width in sorted(settings.BETTY_WIDTHS, reverse=True):

        if abs(last_width - width) < 100:
            # Sometimes the widths are really too close. We only need to check every 100 px
            continue

        if width > 0:
            optimized_buffer.seek(0)
            quality = detect_optimal_quality(optimized_buffer, width)
            image.jpeg_quality_settings[width] = quality

            if quality == settings.BETTY_JPEG_QUALITY_RANGE[-1]:
                # We'are already at max...
                break

        last_width = width

    image.save()
    image.clear_crops()
