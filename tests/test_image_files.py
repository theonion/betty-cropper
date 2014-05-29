import os
import shutil

from django.test import TestCase
from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.cropper.models import Image
from betty.conf.app import settings


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class ImageFileTestCase(TestCase):

    def test_png(self):

        path = os.path.join(TEST_DATA_PATH, "Lenna.png")
        image = Image.objects.create_from_path(path)

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        self.assertTrue(image.source.path.endswith("Lenna.png"))
        self.assertEqual(image.width, 512)
        self.assertEqual(image.height, 512)
        self.assertEqual(image.jpeg_quality, None)
        self.assertTrue(os.path.exists(image.optimized.path))
        self.assertTrue(os.path.exists(image.source.path))

        # Since this image is 512x512, it shouldn't end up getting changed by the optimization process
        self.assertTrue(os.stat(image.optimized.path).st_size, os.stat(image.source.path).st_size)

    def test_jpeg(self):
        path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.jpg")
        image = Image.objects.create_from_path(path)

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        self.assertTrue(image.source.path.endswith("Sam_Hat1.jpg"))
        self.assertEqual(image.width, 3264)
        self.assertEqual(image.height, 2448)
        self.assertEqual(image.jpeg_quality, None)
        self.assertTrue(os.path.exists(image.optimized.path))
        self.assertTrue(os.path.exists(image.source.path))

        source = PILImage.open(image.source.path)
        optimized = PILImage.open(image.optimized.path)

        self.assertEqual(
            source.quantization,
            optimized.quantization
        )

        self.assertEqual(
            JpegImagePlugin.get_sampling(source),
            JpegImagePlugin.get_sampling(optimized),
        )

        # self.assertEqual(os.stat(image.optimized.path).st_size, os.stat(image.source.path).st_size)

    def test_huge_jpeg(self):
        path = os.path.join(TEST_DATA_PATH, "huge.jpg")
        image = Image.objects.create_from_path(path)

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        self.assertTrue(image.source.path.endswith("huge.jpg"))
        self.assertEqual(image.width, 8720)
        self.assertEqual(image.height, 8494)
        self.assertEqual(image.jpeg_quality, None)
        self.assertTrue(os.path.exists(image.optimized.path))
        self.assertTrue(os.path.exists(image.source.path))

        optimized = PILImage.open(image.optimized.path)
        self.assertEqual(optimized.size[0], settings.BETTY_MAX_WIDTH)
        self.assertTrue(os.stat(image.optimized.path).st_size < os.stat(image.source.path).st_size)

    def test_imgmin_upload(self):

        _cached_range = settings.BETTY_JPEG_QUALITY_RANGE
        settings.BETTY_JPEG_QUALITY_RANGE = (60, 95)

        path = os.path.join(TEST_DATA_PATH, "Lenna.png")
        image = Image.objects.create_from_path(path)

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        # Lenna should be a 95 quality, but we'll leave a fudge factor
        self.assertTrue(abs(image.jpeg_quality - 95) < 2)

        settings.BETTY_JPEG_QUALITY_RANGE = _cached_range

    def test_imgmin_upload_lowquality(self):

        _cached_range = settings.BETTY_JPEG_QUALITY_RANGE
        settings.BETTY_JPEG_QUALITY_RANGE = (60, 95)

        path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.jpg")
        image = Image.objects.create_from_path(path)

        settings.BETTY_JPEG_QUALITY_RANGE = _cached_range

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        # This image is already optimized, so this should do nothing.
        self.assertEqual(image.jpeg_quality, None)

    def test_imgmin_large(self):

        _cached_range = settings.BETTY_JPEG_QUALITY_RANGE
        settings.BETTY_JPEG_QUALITY_RANGE = (60, 95)

        path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.png")
        image = Image.objects.create_from_path(path)

        settings.BETTY_JPEG_QUALITY_RANGE = _cached_range

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        # Lenna should be a 95 quality, but we'll leave a fudge factor
        self.assertTrue(abs(image.jpeg_quality - 95) < 2)

    def test_gif_upload(self):

        path = os.path.join(TEST_DATA_PATH, "animated.gif")
        image = Image.objects.create_from_path(path)

        # Re-load the image, now that the task is done
        image = Image.objects.get(id=image.id)

        self.assertEqual(image.width, 256)
        self.assertEqual(image.height, 256)
        self.assertTrue(os.path.exists(image.path()))
        self.assertTrue(os.path.exists(image.source.path))
        self.assertEqual(os.path.basename(image.source.path), "animated.gif")

        self.assertTrue(
            os.path.exists(
                os.path.join(image.path(), "animated/original.gif")
            )
        )

        self.assertTrue(
            os.path.exists(
                os.path.join(image.path(), "animated/original.jpg")
            )
        )

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)

    # def test_large_image_upload(self):
    #     assert self.client.login(username="admin", password=self.password)
    #     image_path = os.path.join(TEST_DATA_PATH, 'huge.jpg')
    #     with open(image_path, "rb") as huge:
    #         data = {"image": huge, "name": "A COOL TRAIN"}
    #         res = self.client.post('/images/api/new', data)
    #     self.assertEqual(res.status_code, 200)
    #     response_json = json.loads(res.content.decode("utf-8"))
    #     self.assertEqual(response_json.get('name'), 'A COOL TRAIN')

    #     image = Image.objects.get(id=response_json['id'])
    #     self.assertTrue(os.path.exists(image.path()))
    #     self.assertTrue(os.path.exists(image.optimized.path))
    #     img = PILImage.open(image.optimized.path)
    #     self.assertEqual(img.size[0], settings.BETTY_MAX_WIDTH)

    #     self.assertEqual(os.path.basename(image.source.path), "huge.jpg")
    #     self.assertEqual(image.name, "A COOL TRAIN")
