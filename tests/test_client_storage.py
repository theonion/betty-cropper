import os

from django.test import LiveServerTestCase
from six.moves.urllib.parse import urljoin

from betty.server.auth import ApiToken
from betty.server.models import Image
from betty.conf.app import settings
from betty.client.storage import BettyCropperStorage

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class StorageTestCase(LiveServerTestCase):

    def setUp(self):
        token = ApiToken.objects.create_standard_user()
        settings.BETTY_PUBLIC_TOKEN = token.public_token
        self.base_url = urljoin("http://localhost:8081", settings.BETTY_IMAGE_URL)
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]

    def test_exists(self):
        image = Image.objects.create(name="Seanna.png", width=512, height=512)

        storage = BettyCropperStorage(base_url=self.base_url)
        self.assertTrue(storage.exists(image.id))

    def test_save(self):
        storage = BettyCropperStorage(base_url=self.base_url)
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, "rb") as lenna:
            image_id = storage.save("Lenna.png", lenna)
            image = Image.objects.get(id=image_id)
            self.assertTrue(image.name, "Lenna.png")
            self.assertTrue(image.width, 512)
            self.assertTrue(image.height, 512)

    def test_url(self):
        image = Image.objects.create(name="Seanna.png", width=512, height=512)

        cropped_url = "{url}/{id}/{ratio}/{width}.{format}".format(
            url=self.base_url,
            id=image.id,
            ratio="original",
            width=600,
            format="jpg"
        )
        storage = BettyCropperStorage(base_url=self.base_url)
        self.assertEqual(storage.url(image.id), cropped_url)
