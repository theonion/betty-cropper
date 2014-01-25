import os
import unittest
import tempfile
import shutil
import json

from betty.flask import app
app.config.update(
    DATABASE = "sqlite://",
    PUBLIC_URL = "http://127.0.0.1:5000",
    RATIOS = ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9"),
    WIDTHS = (80, 150, 240, 300, 320, 400, 480, 620, 640, 820, 960, 1200, 1600),
    API_KEY = 'noop'
)


from betty.flask.models import Image
from betty.core import Ratio
from betty.flask.database import db_session, init_db

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../tests/images')

class BettyTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        image_root = tempfile.mkdtemp()
        app.config.update({
            'IMAGE_ROOT': image_root,
        })
        self.client = app.test_client()  
        init_db()

    def test_ratio_object(self):
        self.assertRaises(ValueError, lambda: Ratio('1x1x2'))
        self.assertRaises(ValueError, lambda: Ratio('3x'))

    def test_image_selections(self):
        image = Image(name="Lenna.gif", width=512, height=512)
        db_session.add(image)
        db_session.commit()

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
        db_session.add(image)
        db_session.commit()

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
        db_session.add(image)
        db_session.commit()
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
        db_session.add(image)
        db_session.commit()
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
        db_session.add(image)
        db_session.commit()
        assert image.get_selection(Ratio('1x1')) == {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}

    def test_missing_file(self):
        image = Image(name="Lenna.gif", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        app.config['PLACEHOLDER'] = True
        res = self.client.get('/%s/1x1/256.jpg' % image.id )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers['Content-Type'], 'image/jpeg')

        res = self.client.get('/%s/original/256.jpg' % image.id )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers['Content-Type'], 'image/jpeg')

        app.config['PLACEHOLDER'] = False
        res = self.client.get('/%s/1x1/256.jpg' % image.id )
        self.assertEqual(res.status_code, 404)


    def test_image_upload(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            headers = [('X-Betty-Api-Key', 'noop')]
            res = self.client.post('/api/new', headers=headers, data=dict(
                image=(lenna, 'Lenna.png'),
            ))

        assert res.status_code == 200
        response_json = json.loads(res.data)
        assert response_json.get('name') == 'Lenna.png'
        assert response_json.get('width') == 512
        assert response_json.get('height') == 512

        image = Image.query.get(response_json['id'])
        assert os.path.exists(image.path())
        assert os.path.exists(image.src_path())

        # Now let's test that a JPEG crop will return properly.
        res = self.client.get('/%s/1x1/256.jpg' % image.id)
        assert res.headers['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), '1x1', '256.jpg'))

        # Now let's test that a PNG crop will return properly.
        res = self.client.get('/%s/1x1/256.png' % image.id)
        assert res.headers['Content-Type'] == 'image/png'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), '1x1', '256.png'))

        # Finally, let's test an "original" crop
        res = self.client.get('/%s/original/256.jpg' % image.id)
        assert res.headers['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), 'original', '256.jpg'))

    def test_bad_image_id(self):
        res = self.client.get('/abc/13x4/256.jpg')
        assert res.status_code == 404

    def test_bad_ratio(self):
        res = self.client.get('/666/13x4/256.jpg')
        assert res.status_code == 404

    def test_bad_extension(self):
        res = self.client.get('/666/1x1/500.gif')
        assert res.status_code == 404

    def test_too_large(self):
        res = self.client.get('/666/1x1/2001.jpg')
        assert res.status_code == 500

    def test_image_redirect(self):
        res = self.client.get('/66666/1x1/100.jpg')
        assert res.status_code == 302
        assert res.headers['Location'] == "http://127.0.0.1:5000/6666/6/1x1/100.jpg"

    def test_placeholder(self):
        app.config['PLACEHOLDER'] = True
        res = self.client.get('/666/1x1/256.jpg')
        assert res.headers['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200

        res = self.client.get('/666/1x1/256.png')
        assert res.headers['Content-Type'] == 'image/png'
        assert res.status_code == 200

        app.config['PLACEHOLDER'] = False
        res = self.client.get('/666/1x1/256.jpg')
        assert res.status_code == 404

    def test_image_js(self):
        res = self.client.get('/image.js')
        assert res.headers['Content-Type'] == 'application/javascript'
        assert res.status_code == 200

    def test_no_api_key(self):
        res = self.client.post('/api/new')
        assert res.status_code == 403

        res = self.client.get('/api/1')
        assert res.status_code == 403        

        res = self.client.post('/api/1/1x1')
        assert res.status_code == 403

        res = self.client.patch('/api/1')
        assert res.status_code == 403

        res = self.client.get('/api/search')
        assert res.status_code == 403

    def test_image_selection_update_api(self):
        image = Image(name="Testing", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        new_selection = {
            'x0': 1,
            'y0': 1,
            'x1': 510,
            'y1': 510
        }
        headers = [('Content-Type', 'application/json'), ('X-Betty-Api-Key', 'noop')]

        res = self.client.post('/api/%s/1x1' % image.id, headers=headers, data=json.dumps(new_selection))
        assert res.status_code == 200

        image = Image.query.get(image.id)
        assert new_selection == image.selections['1x1']

        bad_selection = {
            'x0': 1,
            'x1': 510
        }
        res = self.client.post('/api/%s/1x1' % image.id, headers=headers, data=json.dumps(bad_selection))
        assert res.status_code == 400

        res = self.client.post('/api/%s/original' % image.id, headers=headers, data=json.dumps(bad_selection))
        assert res.status_code == 400

        res = self.client.post('/api/10000/1x1', headers=headers, data=json.dumps(bad_selection))
        assert res.status_code == 404

    def test_image_detail(self):
        image = Image(name="Testing", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        headers = [('X-Betty-Api-Key', 'noop')]
        res = self.client.get('/api/%s' % image.id, headers=headers)
        assert res.status_code == 200

        headers = [('Content-Type', 'application/json'), ('X-Betty-Api-Key', 'noop')]
        res = self.client.patch('/api/%s' % image.id, headers=headers, data=json.dumps({'name': 'Updated'}))
        assert res.status_code == 200

        image = Image.query.get(image.id)
        assert image.name == 'Updated'

    def test_bad_image_data(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            headers = [('X-Betty-Api-Key', 'noop')]
            res = self.client.post('/api/new', headers=headers, data=dict(
                image=(lenna, 'Lenna.png'),
            ))

        assert res.status_code == 200
        response_json = json.loads(res.data)
        assert response_json.get('name') == 'Lenna.png'
        assert response_json.get('width') == 512
        assert response_json.get('height') == 512

        # Now that the image is uploaded, let's fuck up the data.
        image = Image.query.get(response_json['id'])
        image.width = 1024
        image.height = 1024
        db_session.add(image)
        db_session.commit()

        id_string = ""
        for index,char in enumerate(str(image.id)):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        res = self.client.get('%s/1x1/400.jpg' % id_string)
        assert res.status_code == 200

    def test_image_search(self):
        image = Image(name="BLERGH", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        headers = [('X-Betty-Api-Key', 'noop')]
        res = self.client.get('/api/search?q=blergh', headers=headers)
        assert res.status_code == 200

    def tearDown(self):
        shutil.rmtree(app.config['IMAGE_ROOT'])