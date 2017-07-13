import os

from freezegun import freeze_time
import pytest

from django.core.files import File

from betty.cropper.models import Image

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.fixture()
def image(request):
    image = Image.objects.create(
        name="Lenna.png",
        width=512,
        height=512
    )

    lenna = File(open(os.path.join(TEST_DATA_PATH, "Lenna.png"), "rb"))
    image.source.save("Lenna.png", lenna)
    return image


@freeze_time('2016-05-02 01:02:03')
@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_get_png(settings, client, image):

    settings.BETTY_CACHE_CROP_SEC = 123

    res = client.get('/images/{}/source'.format(image.id))
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/png'
    assert res['Last-Modified'] == "Mon, 02 May 2016 01:02:03 GMT"
    assert res['Cache-Control'] == 'max-age=123'
    with open(os.path.join(TEST_DATA_PATH, "Lenna.png"), "rb") as lenna:
        assert res.content == lenna.read()


@pytest.mark.django_db
def test_get_invalid_image(client):
    res = client.get('/images/1/source')
    assert res.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_if_modified_since(settings, client, image):
    settings.BETTY_CACHE_CROP_SEC = 600
    res = client.get('/images/{}/source'.format(image.id),
                     HTTP_IF_MODIFIED_SINCE="Sat, 01 May 2100 00:00:00 GMT")
    assert res.status_code == 304
    assert res['Cache-Control'] == 'max-age=600'
    assert not res.content  # Empty content
