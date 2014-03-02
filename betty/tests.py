import os
import json
import shutil

import pytest
pytestmark = pytest.mark.django_db

from django.test import TestCase, Client
from django.core.files import File

from .conf.app import settings
from .models import Image, Ratio

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), '../tests/images')


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


class APITestCase(TestCase):

    def setUp(self):
        self.client = Client()
        settings.BETTY_API_KEY = "noop"

    def test_no_api_key(self):
        res = self.client.post('/images/api/new')
        self.assertEqual(res.status_code, 403)

        res = self.client.get('/images/api/1')
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/images/api/1/1x1')
        self.assertEqual(res.status_code, 403)

        res = self.client.patch('/images/api/1')
        self.assertEqual(res.status_code, 403)

        res = self.client.get('/images/api/search')
        self.assertEqual(res.status_code, 403)

    def test_image_upload(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            res = self.client.post('/images/api/new', {"image": lenna}, HTTP_X_BETTY_API_KEY="noop")

        self.assertEqual(res.status_code, 200)
        response_json = json.loads(res.content)
        self.assertEqual(response_json.get('name'), 'Lenna.png')
        self.assertEqual(response_json.get('width'), 512)
        self.assertEqual(response_json.get('height'), 512)

        image = Image.objects.get(id=response_json['id'])
        self.assertTrue(os.path.exists(image.path()))
        self.assertTrue(os.path.exists(image.src_path()))

        # Now let's test that a JPEG crop will return properly.
        res = self.client.get('/images/%s/1x1/256.jpg' % image.id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertTrue(os.path.exists(os.path.join(image.path(), '1x1', '256.jpg')))

        # Now let's test that a PNG crop will return properly.
        res = self.client.get('/images/%s/1x1/256.png' % image.id)
        self.assertEqual(res['Content-Type'], 'image/png')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(image.path(), '1x1', '256.png')))

        # Finally, let's test an "original" crop
        res = self.client.get('/images/%s/original/256.jpg' % image.id)
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(image.path(), 'original', '256.jpg')))

    def test_update_selection(self):
        image = Image.objects.create(name="Testing", width=512, height=512)

        new_selection = {
            "x0": 1,
            "y0": 1,
            "x1": 510,
            "y1": 510
        }

        res = self.client.post(
            "/images/api/{0}/1x1".format(image.id),
            data=json.dumps(new_selection),
            content_type="application/json",
            HTTP_X_BETTY_API_KEY="noop"
        )
        self.assertEqual(res.status_code, 200)

        image = Image.objects.get(id=image.id)
        self.assertEqual(new_selection, image.selections['1x1'])

        res = self.client.post(
            "/images/api/{0}/original".format(image.id),
            data=json.dumps(new_selection),
            content_type="application/json",
            HTTP_X_BETTY_API_KEY="noop"
        )
        self.assertEqual(res.status_code, 400)

        bad_selection = {
            'x0': 1,
            'x1': 510
        }
        res = self.client.post(
            "/images/api/{0}/1x1".format(image.id),
            data=json.dumps(bad_selection),
            content_type="application/json",
            HTTP_X_BETTY_API_KEY="noop"
        )
        self.assertEqual(res.status_code, 400)

        res = self.client.post(
            "/images/api/1000001/1x1",
            data=json.dumps(bad_selection),
            content_type="application/json",
            HTTP_X_BETTY_API_KEY="noop"
        )
        self.assertEqual(res.status_code, 404)

    def test_image_detail(self):
        image = Image.objects.create(name="Testing", width=512, height=512)

        res = self.client.get("/images/api/{0}".format(image.id), HTTP_X_BETTY_API_KEY="noop")
        self.assertEqual(res.status_code, 200)

        res = self.client.patch(
            "/images/api/{0}".format(image.id),
            data=json.dumps({"name": "Updated"}),
            content_type="application/json",
            HTTP_X_BETTY_API_KEY="noop"
        )
        self.assertEqual(res.status_code, 200)

        image = Image.objects.get(id=image.id)
        self.assertEqual(image.name, "Updated")

    def test_image_search(self):
        image = Image.objects.create(name="BLERGH", width=512, height=512)

        res = self.client.get('/images/api/search?q=blergh', HTTP_X_BETTY_API_KEY="noop")
        self.assertEqual(res.status_code, 200)
        results = json.loads(res.content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], image.id)

    def test_bad_image_data(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            res = self.client.post('/images/api/new', {"image": lenna}, HTTP_X_BETTY_API_KEY="noop")

        self.assertEqual(res.status_code, 200)
        response_json = json.loads(res.content)
        self.assertEqual(response_json.get("name"), "Lenna.png")
        self.assertEqual(response_json.get("width"), 512)
        self.assertEqual(response_json.get("height"), 512)

        # Now that the image is uploaded, let's fuck up the data.
        image = Image.objects.get(id=response_json['id'])
        image.width = 1024
        image.height = 1024
        image.save()

        id_string = ""
        for index, char in enumerate(str(image.id)):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        res = self.client.get('/images/{0}/1x1/400.jpg'.format(id_string))
        assert res.status_code == 200

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
