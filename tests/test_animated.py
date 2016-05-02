import os

from freezegun import freeze_time
import pytest

from django.core.files import File

from betty.cropper.models import Image

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.fixture()
def image(request):
    image = Image.objects.create(
        name="animated.gif",
        width=512,
        height=512,
        animated=True,
    )

    lenna = File(open(os.path.join(TEST_DATA_PATH, "animated.gif"), "rb"))
    image.source.save("animated.gif", lenna)
    return image


@freeze_time('2016-05-02 01:02:03')
@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_get_jpg(client, image):
    res = client.get('/images/{}/animated/original.jpg'.format(image.id))
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/jpeg'
    assert res['Last-Modified'] == "Mon, 02 May 2016 01:02:03 GMT"
    saved_path = os.path.join(image.path(), 'animated/original.jpg')
    assert os.path.exists(saved_path)


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_get_animated_gif(client, image):
    res = client.get('/images/{}/animated/original.gif'.format(image.id))
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/gif'
    saved_path = os.path.join(image.path(), 'animated/original.gif')
    assert os.path.exists(saved_path)


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_get_unsupported_extension(client, image):
    res = client.get('/images/{}/animated/original.png'.format(image.id))
    assert res.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_get_not_animated(client, image):
    image.animated = False
    image.save()
    res = client.get('/images/{}/animated/original.gif'.format(image.id))
    assert res.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_get_invalid_image(client):
    res = client.get('/images/1/animated/original.gif')
    assert res.status_code == 404


def test_get_animated_url():
    image = Image(id=1)
    assert '/images/1/animated/original.gif' == image.get_animated_url(extension='gif')
    assert '/images/1/animated/original.jpg' == image.get_animated_url(extension='jpg')


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_if_modified_since(settings, client, image):
    settings.BETTY_CACHE_CROP_SEC = 600
    res = client.get('/images/{}/animated/original.gif'.format(image.id),
                     HTTP_IF_MODIFIED_SINCE="Sat, 01 May 2100 00:00:00 GMT")
    assert res.status_code == 304
    assert res['Cache-Control'] == 'max-age=600'
    assert not res.content  # Empty content
