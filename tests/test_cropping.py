import os
import shutil

import pytest

from django.core.files import File

from betty.conf.app import settings
from betty.cropper.models import Image, Ratio

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.fixture()
def clean_image_root(request):
    # Also does it on startup too, until we cleanup all test cased to cleanup properly
    shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)

    def cleanup():
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
    request.addfinalizer(cleanup)


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
    image = Image.objects.create(name="Lenna.gif", width=512, height=512)

    res = client.get('/images/{0}/1x1/256.jpg'.format(image.id))
    assert res.status_code == 500


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_image_save(client):

    image = Image.objects.create(
        name="Lenna.png",
        width=512,
        height=512
    )
    lenna = File(open(os.path.join(TEST_DATA_PATH, "Lenna.png"), "rb"))
    image.source.save("Lenna.png", lenna)

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
def test_disable_crop_save(client, settings):
    settings.BETTY_SAVE_CROPS = False

    image = Image.objects.create(
        name="Lenna.png",
        width=512,
        height=512
    )
    lenna = File(open(os.path.join(TEST_DATA_PATH, "Lenna.png"), "rb"))
    image.source.save("Lenna.png", lenna)

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
