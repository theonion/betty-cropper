import os

from django.test import LiveServerTestCase
from django.utils.six.moves.urllib.parse import urljoin

from betty.server.auth import ApiToken
from betty.server.models import Image
from betty.conf.app import settings
from betty.client.storage import BettyCropperStorage

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class StorageTestCase(LiveServerTestCase):

    def setUp(self):
        token = ApiToken.objects.create_standard_user()
        settings.BETTY_PUBLIC_TOKEN = token.public_token
        settings.BETTY_IMAGE_URL = urljoin("http://localhost:8081", settings.BETTY_IMAGE_URL)

    def test_exists(self):
        image = Image.objects.create(name="Seanna.png", width=512, height=512)

        storage = BettyCropperStorage()
        self.assertTrue(storage.exists(image.id))

    def test_url(self):
        image = Image.objects.create(name="Seanna.png", width=512, height=512)
        base_url = settings.BETTY_IMAGE_URL
        if base_url[-1] == "/":
            base_url = base_url[:-1]

        cropped_url = "{url}/{id}/{ratio}/{width}.{format}".format(
            url=base_url,
            id=image.id,
            ratio="original",
            width=600,
            format="jpg"
        )
        storage = BettyCropperStorage()
        self.assertEqual(storage.url(image.id), cropped_url)
