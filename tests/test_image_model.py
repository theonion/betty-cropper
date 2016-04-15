import os

from mock import call, patch
import pytest

from django.core.files import File

from betty.cropper.models import Image, Ratio


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.fixture()
def image(request):
    image = Image.objects.create(name="Testing", width=512, height=512)
    lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
    with open(lenna_path, "rb") as lenna:
        image.source.save('Lenna', File(lenna))
    return image


def make_some_crops(image, settings):
    settings.BETTY_RATIOS = ["1x1", "3x1", "16x9"]
    settings.BETTY_WIDTHS = [200, 400]

    # Crops that would be saved (if enabled)
    image.crop(ratio=Ratio('1x1'), width=200, extension='png')
    image.crop(ratio=Ratio('16x9'), width=400, extension='jpg')
    # Not saved to disk (not in WIDTH list)
    image.crop(ratio=Ratio('16x9'), width=401, extension='jpg')

    return image


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
@pytest.mark.parametrize('save_crops', [True, False])  # Test setting enabled + disabled
def test_image_clear_crops(image, settings, save_crops):

    settings.BETTY_SAVE_CROPS_TO_DISK = save_crops
    settings.BETTY_CACHE_FLUSHER = 'tests.test_image_model.test_flush'

    make_some_crops(image, settings)

    with patch('betty.cropper.models.settings.BETTY_CACHE_FLUSHER') as mock_flusher:
        with patch('shutil.rmtree') as mock_rmtree:

            image.clear_crops()

            # Flushes all supported crop combinations
            mock_flusher.assert_called_with([
                '/images/{image_id}/{ratio}/{width}.{extension}'.format(image_id=image.id,
                                                                        width=width,
                                                                        ratio=ratio,
                                                                        extension=extension)
                for ratio in ['1x1', '3x1', '16x9', 'original']
                for extension in ['png', 'jpg']
                for width in [200, 400]])

            assert mock_rmtree.called == save_crops
            if save_crops:
                # Filesystem deletes entire directories if they exist
                image_dir = os.path.join(settings.BETTY_IMAGE_ROOT, str(image.id))
                assert sorted(mock_rmtree.call_args_list) == sorted(
                    [call(os.path.join(image_dir, '1x1')),
                     call(os.path.join(image_dir, '16x9'))])


@pytest.mark.django_db
def test_get_width(image):
    image.width = 0
    with patch('django.core.files.storage.open', create=True) as mock_open:
        mock_open.side_effect = lambda path, mode: open(path, mode)
        for _ in range(2):
            assert 512 == image.get_width()
            assert mock_open.call_count == 1


@pytest.mark.django_db
def test_get_height(image):
    image.height = 0
    with patch('django.core.files.storage.open', create=True) as mock_open:
        mock_open.side_effect = lambda path, mode: open(path, mode)
        for _ in range(2):
            assert 512 == image.get_height()
            assert mock_open.call_count == 1


@pytest.mark.django_db
def test_refresh_dimensions(image):
    image.height = 0
    image.width = 0
    with patch('django.core.files.storage.open', create=True) as mock_open:
        mock_open.side_effect = lambda path, mode: open(path, mode)
        image._refresh_dimensions()
        assert image.width == 512
        assert image.get_width() == 512
