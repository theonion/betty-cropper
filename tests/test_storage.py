import json
import os

import pytest

from inmemorystorage.storage import InMemoryStorage

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.mark.django_db
def test_alternate_storage(admin_client, settings):
    """Verify can plugin alternate storage backend"""

    settings.DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'
    settings.BETTY_SAVE_CROPS_TO_DISK = False
    settings.BETTY_IMAGE_ROOT = 'images'

    # Create Image
    path = os.path.join(TEST_DATA_PATH, 'animated.gif')
    with open(path, "rb") as image:
        resp = admin_client.post('/images/api/new', {"image": image})
    assert resp.status_code == 200
    image_id = json.loads(resp.content.decode("utf-8"))['id']

    # Storage lazy loaded after first access
    from django.core.files.storage import default_storage
    assert isinstance(default_storage._wrapped, InMemoryStorage)  # 'Using alternate storage'

    assert default_storage.filesystem.exists('images/{}/animated.gif'.format(image_id))
    assert default_storage.filesystem.exists('images/{}/optimized.gif'.format(image_id))

    # Delete Image
    resp = admin_client.post("/images/api/{0}".format(image_id),
                             REQUEST_METHOD="DELETE")

    assert not default_storage.filesystem.exists('images/{}/animated.gif'.format(image_id))
    assert not default_storage.filesystem.exists('images/{}/optimized.gif'.format(image_id))
