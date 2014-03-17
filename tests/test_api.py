import os
import json
import shutil

from django.test import TestCase, Client

from django.contrib.auth.models import User

from betty.conf.app import settings
from betty.cropper.models import Image

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class PatchClient(Client):
    def patch(self, *args, **kwargs):
        kwargs["REQUEST_METHOD"] = "PATCH"
        return super(PatchClient, self).post(*args, **kwargs)


class APITestCase(TestCase):

    def setUp(self):
        self.password = User.objects.make_random_password()
        user = User.objects.create_superuser(
            username="admin",
            email="tech@theonion.com",
            password=self.password
        )
        user.save()
        self.client = PatchClient()

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
        assert self.client.login(username="admin", password=self.password)

        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, "rb") as lenna:
            data = {"image": lenna, "name": "LENNA DOT PNG", "credit": "Playboy"}
            res = self.client.post('/images/api/new', data)
        self.assertEqual(res.status_code, 200)
        response_json = json.loads(res.content.decode("utf-8"))
        self.assertEqual(response_json.get('name'), 'LENNA DOT PNG')
        self.assertEqual(response_json.get('credit'), 'Playboy')
        self.assertEqual(response_json.get('width'), 512)
        self.assertEqual(response_json.get('height'), 512)

        image = Image.objects.get(id=response_json['id'])
        self.assertTrue(os.path.exists(image.path()))
        self.assertTrue(os.path.exists(image.src_path()))
        self.assertEqual(os.path.basename(image.src_path()), "Lenna.png")
        self.assertEqual(image.name, "LENNA DOT PNG")
        self.assertEqual(image.credit, "Playboy")

        # Now let's test that a JPEG crop will return properly.
        res = self.client.get("/images/{}/1x1/240.jpg".format(image.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "image/jpeg")
        self.assertTrue(os.path.exists(os.path.join(image.path(), '1x1', '240.jpg')))

    def test_update_selection(self):
        assert self.client.login(username="admin", password=self.password)

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
        )
        self.assertEqual(res.status_code, 200)

        image = Image.objects.get(id=image.id)
        self.assertEqual(new_selection, image.selections['1x1'])

        res = self.client.post(
            "/images/api/{0}/original".format(image.id),
            data=json.dumps(new_selection),
            content_type="application/json",
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
        )
        self.assertEqual(res.status_code, 400)

        res = self.client.post(
            "/images/api/1000001/1x1",
            data=json.dumps(bad_selection),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 404)

    def test_image_detail(self):
        assert self.client.login(username="admin", password=self.password)
        image = Image.objects.create(name="Testing", width=512, height=512)

        res = self.client.get("/images/api/{0}".format(image.id))
        self.assertEqual(res.status_code, 200)

        res = self.client.patch(
            "/images/api/{0}".format(image.id),
            data=json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)

        image = Image.objects.get(id=image.id)
        self.assertEqual(image.name, "Updated")

    def test_image_search(self):
        assert self.client.login(username="admin", password=self.password)
        image = Image.objects.create(name="BLERGH", width=512, height=512)

        res = self.client.get('/images/api/search?q=blergh')
        self.assertEqual(res.status_code, 200)
        results = json.loads(res.content.decode("utf-8"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], image.id)

    def test_bad_image_data(self):
        assert self.client.login(username="admin", password=self.password)
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, "rb") as lenna:
            res = self.client.post('/images/api/new', {"image": lenna})

        self.assertEqual(res.status_code, 200)
        response_json = json.loads(res.content.decode("utf-8"))
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
