
from django.core.management.base import BaseCommand

from betty.cropper.models import Image
from betty.cropper.tasks import search_image_quality, optimize_image


class Command(BaseCommand):
    help = 'Creates optimal image files, and figures out the best JPEG quality level for each image'

    def handle(self, *args, **options):
        for image in Image.objects.iterator():
            if not image.source.name:
                continue

            if not image.optimized.name:
                optimize_image.apply(args=(image.id,))

            if image.jpeg_quality is None:
                search_image_quality.apply(args=(image.id,))
