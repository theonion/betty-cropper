import os
import psutil
import shutil

from betty.cropper.models import Image
from betty.conf.app import settings as bettysettings

import pytest

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


def get_open_files(process):
    files = process.open_files()
    # Ignore IPython dev files
    return [f for f in files
            if not f.path.endswith('/.ipython/profile_default/history.sqlite')]


@pytest.mark.django_db
def test_imgmin_upload(settings):
    shutil.rmtree(bettysettings.BETTY_IMAGE_ROOT, ignore_errors=True)

    settings.BETTY_JPEG_QUALITY_RANGE = (60, 92)

    path = os.path.join(TEST_DATA_PATH, "Lenna.png")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert len(image.jpeg_quality_settings) > 1

    # Make sure that we closed all the files
    process = psutil.Process(os.getpid())
    assert len(get_open_files(process)) == 0


@pytest.mark.django_db
def test_imgmin_cartoon(settings):
    shutil.rmtree(bettysettings.BETTY_IMAGE_ROOT, ignore_errors=True)

    settings.BETTY_JPEG_QUALITY_RANGE = (60, 92)

    path = os.path.join(TEST_DATA_PATH, "Simpsons-Week_a.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    # this is a cartoon, so we should get 92 across the board
    assert image.jpeg_quality_settings == {
        "1200": 92,
    }

    # Make sure that we closed all the files
    process = psutil.Process(os.getpid())
    print(get_open_files(process))
    assert len(get_open_files(process)) == 0


@pytest.mark.django_db
def test_imgmin_upload_lowquality(settings):
    shutil.rmtree(bettysettings.BETTY_IMAGE_ROOT, ignore_errors=True)

    settings.BETTY_JPEG_QUALITY_RANGE = (60, 92)

    path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    # This image is already optimized, so this should do nothing.
    assert image.jpeg_quality_settings is None

    # Make sure that we closed all the files
    process = psutil.Process(os.getpid())
    print(get_open_files(process))
    assert len(get_open_files(process)) == 0
