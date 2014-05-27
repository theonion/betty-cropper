import os

from django.core.management.base import BaseCommand
from PIL import Image as PILImage

from betty.cropper.models import Image
from betty.cropper.tasks import search_image_quality
from betty.conf.app import settings


class Command(BaseCommand):
    help = 'Creates optimal image files, and figures out the best JPEG quality level for each image'

    def handle(self, *args, **options):
        for image in Image.objects.iterator():
            if image.optimized is None:
                img = PILImage.open(image.source.path)
                icc_profile = img.info.get("icc_profile")
                
                if img.size[0] > (settings.BETTY_MAX_WIDTH * 2):
                    height = settings.BETTY_MAX_WIDTH * float(img.size[1]) / float(img.size[0])
                    img = img.resize((settings.BETTY_MAX_WIDTH, int(round(height))), PILImage.ANTIALIAS)

                optimized_path = os.path.join(image.path(), "optimized.png")
                img.save(optimized_path, "PNG", icc_profile=icc_profile)
                image.optimized.name = optimized_path
                image.save()

            if image.jpeg_quality == 80:
                search_image_quality(image.id)
