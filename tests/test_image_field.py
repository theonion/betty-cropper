import os
import shutil

from six.moves.urllib.parse import urljoin

from django.core.files import File
from django.test import LiveServerTestCase

from betty.authtoken.models import ApiToken
from betty.cropper.models import Image
from betty.conf.app import settings
from tests.testapp.models import TestModel

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class ImageFieldTestCase(LiveServerTestCase):

    def setUp(self):
        token = ApiToken.objects.create_standard_user()
        settings.BETTY_PUBLIC_TOKEN = token.public_token
        self.base_url = urljoin("http://localhost:8081", settings.BETTY_IMAGE_URL)
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]
        settings.BETTY_IMAGE_URL = self.base_url

    def test_save(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, "rb") as lenna:
            test = TestModel()
            test.image.save("Lenna.png", File(lenna))
        image = Image.objects.get(id=test.image.id)
        self.assertEqual(test.image.name, "Lenna.png")
        self.assertEqual(image.name, "Lenna.png")

        test = TestModel.objects.get(id=test.id)
        self.assertEqual(test.image.name, "Lenna.png")

    def test_alt_and_caption(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, "rb") as lenna:
            test = TestModel()
            test.image.save("Lenna.png", File(lenna))

        test.image.alt = "Just a cool chick"
        test.image.caption = "Kind of sexist?"
        test.save()

        test = TestModel.objects.get(id=test.id)

        self.assertEqual(test.image.alt, "Just a cool chick")
        self.assertEqual(test.image.caption, "Kind of sexist?")

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT)
