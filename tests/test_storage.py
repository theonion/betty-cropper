import json
import os

from mock import patch
import pytest

from inmemorystorage.storage import InMemoryStorage

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.mark.django_db
def test_alternate_storage(admin_client, settings):
    """Verify can plugin alternate storage backend"""

    settings.BETTY_IMAGE_ROOT = 'images'

    storage = InMemoryStorage()
    with patch('django.db.models.fields.files.default_storage._wrapped', storage):

        # Create Image
        path = os.path.join(TEST_DATA_PATH, 'lenna.png')
        with open(path, "rb") as image:

            resp = admin_client.post('/images/api/new', {"image": image})
            assert resp.status_code == 200
            image_id = json.loads(resp.content.decode("utf-8"))['id']

            image.seek(0)
            image_data = image.read()
            storage_data = storage.filesystem.open('images/{}/lenna.png'.format(image_id)).read()
            assert image_data == storage_data
            assert storage.filesystem.exists('images/{}/optimized.png'.format(image_id))

        # Delete Image
        resp = admin_client.post("/images/api/{0}".format(image_id),
                                 REQUEST_METHOD="DELETE")

        assert not storage.filesystem.exists('images/{}/lenna.png'.format(image_id))
        assert not storage.filesystem.exists('images/{}/optimized.png'.format(image_id))
