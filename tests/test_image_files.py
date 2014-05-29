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

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)

    # def test_imgmin_upload(self):
    #     assert self.client.login(username="admin", password=self.password)

    #     _cached_range = settings.BETTY_JPEG_QUALITY_RANGE
    #     settings.BETTY_JPEG_QUALITY_RANGE = (60, 95)

    #     lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
    #     with open(lenna_path, "rb") as lenna:
    #         data = {"image": lenna, "name": "LENNA DOT PNG", "credit": "Playboy"}
    #         res = self.client.post('/images/api/new', data)
    #     self.assertEqual(res.status_code, 200)

    #     response_json = json.loads(res.content.decode("utf-8"))
    #     image = Image.objects.get(id=response_json['id'])
    #     self.assertEqual(image.jpeg_quality, 95)

    #     settings.BETTY_JPEG_QUALITY_RANGE = _cached_range

    # def test_imgmin_upload_lowquality(self):
    #     assert self.client.login(username="admin", password=self.password)

    #     _cached_range = settings.BETTY_JPEG_QUALITY_RANGE
    #     settings.BETTY_JPEG_QUALITY_RANGE = (60, 95)

    #     sam_path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.jpg")
    #     with open(sam_path, "rb") as image:
    #         data = {"image": image, "name": "some guy walking"}
    #         res = self.client.post('/images/api/new', data)
    #     self.assertEqual(res.status_code, 200)

    #     response_json = json.loads(res.content.decode("utf-8"))
    #     image = Image.objects.get(id=response_json["id"])
    #     self.assertTrue(os.path.exists(image.optimized.path))

    #     self.assertEqual(image.jpeg_quality, None)

    #     settings.BETTY_JPEG_QUALITY_RANGE = _cached_range

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

    # def test_gif_upload(self):
    #     assert self.client.login(username="admin", password=self.password)
    #     image_path = os.path.join(TEST_DATA_PATH, 'animated.gif')
    #     with open(image_path, "rb") as gif:
    #         data = {"image": gif, "name": "Some science shit"}
    #         res = self.client.post('/images/api/new', data)
    #     self.assertEqual(res.status_code, 200)
    #     response_json = json.loads(res.content.decode("utf-8"))
    #     self.assertEqual(response_json.get('name'), 'Some science shit')
    #     self.assertEqual(response_json.get('width'), 256)
    #     self.assertEqual(response_json.get('height'), 256)

    #     image = Image.objects.get(id=response_json['id'])
    #     self.assertTrue(os.path.exists(image.path()))
    #     self.assertTrue(os.path.exists(image.source.path))
    #     self.assertEqual(os.path.basename(image.source.path), "animated.gif")

    #     self.assertTrue(
    #         os.path.exists(
    #             os.path.join(image.path(), "animated/original.gif")
    #         )
    #     )

    #     self.assertTrue(
    #         os.path.exists(
    #             os.path.join(image.path(), "animated/original.jpg")
    #         )
    #     )

    #     self.assertEqual(image.name, "Some science shit")