import os

from django.core.management.base import BaseCommand
from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.cropper.models import Image, optimized_upload_to
from betty.cropper.tasks import search_image_quality
from betty.conf.app import settings


class Command(BaseCommand):
    help = 'Creates optimal image files, and figures out the best JPEG quality level for each image'

    def handle(self, *args, **options):
        for image in Image.objects.iterator():
            if not image.optimized.name:
                img = PILImage.open(image.source.path)
                icc_profile = img.info.get("icc_profile")
                if img.format == "JPEG":
                    qtables = img.quantization
                    subsampling = JpegImagePlugin.get_sampling(img)
                
                if img.size[0] > (settings.BETTY_MAX_WIDTH * 2):
                    height = settings.BETTY_MAX_WIDTH * float(img.size[1]) / float(img.size[0])
                    img = img.resize((settings.BETTY_MAX_WIDTH, int(round(height))), PILImage.ANTIALIAS)

                filename = os.path.split(image.source.path)[1]
                optimized_path = optimized_upload_to(image, filename)
                if img.format == "JPEG":
                    # For JPEG files, we need to make sure that we keep the quantization profile
                    img.save(
                        optimized_path,
                        icc_profile=icc_profile,
                        qtables=qtables,
                        subsampling=subsampling)
                else:
                    img.save(optimized_path, icc_profile=icc_profile)

                image.optimized.name = optimized_path
                image.save()

            if image.jpeg_quality is None:
                search_image_quality(image.id)
