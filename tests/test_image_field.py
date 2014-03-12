import os

from six.moves.urllib.parse import urljoin

from django.core.files import File
from django.test import LiveServerTestCase

from betty.server.auth import ApiToken
from betty.server.models import Image
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
