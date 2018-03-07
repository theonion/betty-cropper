import io
import os

from freezegun import freeze_time
from PIL import Image as PILImage
import pytest

from django.core.files import File

from betty.conf.app import settings
from betty.cropper.models import Image, Ratio

from mock import patch


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@freeze_time('2016-05-02 01:02:03')
@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_basic_cropping(settings, client, image):
    settings.BETTY_CACHE_CROP_SEC = 600
    res = client.get('/images/{}/1x1/200.jpg'.format(image.id))
    assert res.status_code == 200
    assert res['Cache-Control'] == 'max-age=600'
    assert res['Last-Modified'] == "Mon, 02 May 2016 01:02:03 GMT"
    assert res['Content-Type'] == "image/jpeg"

    image_buffer = io.BytesIO(res.content)
    img = PILImage.open(image_buffer)
    assert img.size == (200, 200)


@pytest.mark.django_db
def test_image_selections():

    image = Image.objects.create(
        name="Lenna.gif",
        width=512,
        height=512
    )

    # Test to make sure the default selections work
    assert image.get_selection(Ratio('1x1')) == {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}

    # Now let's add some bad data
    image.selections = {
        '1x1': {
            'x0': 0,
            'y0': 0,
            'x1': 513,
            'y1': 512
        }
    }
    image.save()

    # Now, that was a bad selection, so we should be getting an auto generated one.
    assert image.get_selection(Ratio('1x1')) == {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}

    # Try with a negative value
    image.selections = {
        '1x1': {
            'x0': -1,
            'y0': 0,
            'x1': 512,
            'y1': 512
        }
    }
    image.save()
    assert image.get_selection(Ratio('1x1')) == {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}

    # Try with another negative value
    image.selections = {
        '1x1': {
            'x0': 0,
            'y0': 0,
            'x1': -1,
            'y1': 512
        }
    }
    image.save()
    assert image.get_selection(Ratio('1x1')) == {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}

    # Try with bad x values
    image.selections = {
        '1x1': {
            'x0': 10,
            'y0': 0,
            'x1': 9,
            'y1': 512
        }
    }
    image.save()
    assert image.get_selection(Ratio('1x1')) == {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}


def test_bad_image_id(client):
    res = client.get('/images/abc/13x4/256.jpg')
    assert res.status_code == 404


def test_bad_ratio(client):
    res = client.get('/images/666/13x4/256.jpg')
    assert res.status_code == 404


def test_malformed_ratio(client):
    res = client.get('/images/666/farts/256.jpg')
    assert res.status_code == 404


def test_bad_extension(client):
    res = client.get('/images/666/1x1/500.gif')
    assert res.status_code == 404

    res = client.get('/images/666/1x1/500.pngbutts')
    assert res.status_code == 404


def test_too_large(client):
    res = client.get("/images/666/1x1/{}.jpg".format(settings.BETTY_MAX_WIDTH + 1))
    assert res.status_code == 500


def test_image_redirect(client):
    res = client.get('/images/666666/1x1/100.jpg')
    assert res.status_code == 302
    assert res['Location'].endswith("/images/6666/66/1x1/100.jpg")


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


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_crop_caching(settings, client, image):

    settings.BETTY_CACHE_CROP_SEC = 1234
    settings.BETTY_CACHE_CROP_NON_BREAKPOINT_SEC = 456
    settings.BETTY_WIDTHS = [100]
    settings.BETTY_CLIENT_ONLY_WIDTHS = [200]

    # Breakpoint
    for width in [100, 200]:
        res = client.get('/images/{image_id}/1x1/{width}.jpg'.format(image_id=image.id,
                                                                     width=width))
        assert res.status_code == 200
        assert res['Cache-Control'] == 'max-age=1234'

    # Non-Breakpoint
    res = client.get('/images/{}/1x1/300.jpg'.format(image.id))
    assert res.status_code == 200
    assert res['Cache-Control'] == 'max-age=456'


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_crop_caching_default_non_breakpoint(settings, client, image):

    settings.BETTY_CACHE_CROP_SEC = 1234

    # BETTY_CACHE_CROP_NON_BREAKPOINT_SEC not set, uses BETTY_CACHE_CROP_SEC
    res = client.get('/images/{}/1x1/100.jpg'.format(image.id))
    assert res.status_code == 200
    assert res['Cache-Control'] == 'max-age=1234'


@pytest.mark.django_db
def test_placeholder(settings, client):
    settings.BETTY_PLACEHOLDER = True

    res = client.get('/images/666/original/256.jpg')
    assert res['Content-Type'] == 'image/jpeg'
    assert res.status_code == 200

    res = client.get('/images/666/1x1/256.jpg')
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/jpeg'

    res = client.get('/images/666/1x1/256.png')
    assert res['Content-Type'] == 'image/png'
    assert res.status_code == 200

    settings.BETTY_PLACEHOLDER = False
    res = client.get('/images/666/1x1/256.jpg')
    assert res.status_code == 404


@pytest.mark.django_db
def test_missing_file(client):
    with patch('betty.cropper.views.logger') as mock_logger:
        image = Image.objects.create(name="Lenna.gif", width=512, height=512)

        res = client.get('/images/{0}/1x1/256.jpg'.format(image.id))
        assert res.status_code == 500
        assert mock_logger.exception.call_args[0][0].startswith('Cropping error')


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_image_save(client, image):

    # Now let's test that a JPEG crop will return properly.
    res = client.get('/images/{}/1x1/240.jpg'.format(image.id))
    assert res['Content-Type'] == 'image/jpeg'
    assert res.status_code == 200
    assert os.path.exists(os.path.join(image.path(), '1x1', '240.jpg'))

    # Now let's test that a PNG crop will return properly.
    res = client.get('/images/{}/1x1/240.png'.format(image.id))
    assert res['Content-Type'] == 'image/png'
    assert res.status_code == 200
    assert os.path.exists(os.path.join(image.path(), '1x1', '240.png'))

    # Let's test an "original" crop
    res = client.get('/images/{}/original/240.jpg'.format(image.id))
    assert res['Content-Type'] == 'image/jpeg'
    assert res.status_code == 200
    assert os.path.exists(os.path.join(image.path(), 'original', '240.jpg'))

    # Finally, let's test a width that doesn't exist
    res = client.get('/images/{}/original/666.jpg'.format(image.id))
    res['Content-Type'] == 'image/jpeg'
    assert res.status_code == 200
    assert not os.path.exists(os.path.join(image.path(), 'original', '666.jpg'))


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_disable_crop_save(client, settings, image):
    settings.BETTY_SAVE_CROPS_TO_DISK = False

    # Now let's test that a JPEG crop will return properly.
    res = client.get('/images/{}/1x1/240.jpg'.format(image.id))
    assert res['Content-Type'] == 'image/jpeg'
    assert res.status_code == 200
    # Verify crop not saved to disk
    assert not os.path.exists(os.path.join(image.path(), '1x1', '240.jpg'))


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_non_rgb(client):

    image = Image.objects.create(
        name="animated.gif",
        width=512,
        height=512
    )

    lenna = File(open(os.path.join(TEST_DATA_PATH, "animated.gif"), "rb"))
    image.source.save("animated.gif", lenna)

    res = client.get('/images/{}/1x1/240.jpg'.format(image.id))
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/jpeg'
    cropped_path = os.path.join(image.path(), '1x1/240.jpg')
    assert os.path.exists(cropped_path)

    res = client.get('/images/{}/original/1200.jpg'.format(image.id))
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/jpeg'
    assert os.path.exists(os.path.join(image.path(), 'original/1200.jpg'))


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_jpg_cmyk_to_png(client):

    image = Image.objects.create(
        name="Lenna_cmyk.jpg",
        width=512,
        height=512
    )

    lenna = File(open(os.path.join(TEST_DATA_PATH, "Lenna_cmyk.jpg"), "rb"))
    image.source.save("Lenna_cmyk.jpg", lenna)

    res = client.get('/images/{}/original/1200.png'.format(image.id))
    assert res.status_code == 200
    assert res['Content-Type'] == 'image/png'
    assert os.path.exists(os.path.join(image.path(), 'original/1200.png'))


def test_image_js(settings, client):
    settings.BETTY_WIDTHS = [100, 200]
    settings.BETTY_CLIENT_ONLY_WIDTHS = [2, 1]
    settings.BETTY_IMAGE_URL = 'http://test.example.org/images'
    res = client.get("/images/image.js")
    assert res.status_code == 200
    assert res['Content-Type'] == 'application/javascript'
    # Sorted + appends '0' if missing
    assert res.context['BETTY_WIDTHS'] == [0, 1, 2, 100, 200]
    assert res.context['BETTY_IMAGE_URL'] == '//test.example.org/images'


def test_image_js_use_request_host(settings, client):
    settings.BETTY_IMAGE_URL = 'http://test.example.org/images'
    settings.BETTY_IMAGE_URL_USE_REQUEST_HOST = True
    res = client.get("/images/image.js", SERVER_NAME='alt.example.org')
    assert res.status_code == 200
    assert res.context['BETTY_IMAGE_URL'] == '//alt.example.org/images'


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_if_modified_since(settings, client, image):
    settings.BETTY_CACHE_CROP_SEC = 600
    res = client.get('/images/{}/1x1/300.jpg'.format(image.id),
                     HTTP_IF_MODIFIED_SINCE="Sat, 01 May 2100 00:00:00 GMT")
    assert res.status_code == 304
    assert res['Cache-Control'] == 'max-age=600'
    assert not res.content  # Empty content
