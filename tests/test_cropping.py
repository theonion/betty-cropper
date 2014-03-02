import os
import shutil

from django.test import TestCase, Client
from django.core.files import File
from django.contrib.auth import get_user_model
User = get_user_model()

from betty.conf.app import settings
from betty.models import Image, Ratio

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class ImageSavingTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_image_selections(self):
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

    def test_bad_image_id(self):
        res = self.client.get('/images/abc/13x4/256.jpg')
        assert res.status_code == 404

    def test_bad_ratio(self):
        res = self.client.get('/images/666/13x4/256.jpg')
        assert res.status_code == 404

    def test_bad_extension(self):
        res = self.client.get('/images/666/1x1/500.gif')
        assert res.status_code == 404

    def test_too_large(self):
        res = self.client.get('/images/666/1x1/2001.jpg')
        assert res.status_code == 500

    def test_image_redirect(self):
        res = self.client.get('/images/66666/1x1/100.jpg')
        self.assertRedirects(res, "/images/6666/6/1x1/100.jpg", target_status_code=404)

    def test_placeholder(self):
        settings.BETTY_PLACEHOLDER = True

        res = self.client.get('/images/666/original/256.jpg')
        assert res['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200

        res = self.client.get('/images/666/1x1/256.jpg')
        assert res.status_code == 200
        assert res['Content-Type'] == 'image/jpeg'

        res = self.client.get('/images/666/1x1/256.png')
        assert res['Content-Type'] == 'image/png'
        assert res.status_code == 200

        settings.BETTY_PLACEHOLDER = False
        res = self.client.get('/images/666/1x1/256.jpg')
        assert res.status_code == 404

    def test_missing_file(self):
        image = Image.objects.create(name="Lenna.gif", width=512, height=512)

        res = self.client.get('/images/{0}/1x1/256.jpg'.format(image.id))
        self.assertEqual(res.status_code, 500)

    def test_image_save(self):

        image = Image.objects.create(
            name="Lenna.png",
            width=512,
            height=512
        )
        lenna = File(open(os.path.join(TEST_DATA_PATH, "Lenna.png"), "r"))
        image.source.save("Lenna.png", lenna)

        # Now let's test that a JPEG crop will return properly.
        res = self.client.get('/images/%s/1x1/256.jpg' % image.id)
        assert res['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), '1x1', '256.jpg'))

        # Now let's test that a PNG crop will return properly.
        res = self.client.get('/images/%s/1x1/256.png' % image.id)
        assert res['Content-Type'] == 'image/png'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), '1x1', '256.png'))

        # Finally, let's test an "original" crop
        res = self.client.get('/images/%s/original/256.jpg' % image.id)
        assert res['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), 'original', '256.jpg'))

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
