import os
import unittest
import tempfile
import shutil
import json

from sqlalchemy.orm import scoped_session, sessionmaker

from betty import app
from betty.models import Image
from betty.database import init_db, db_session

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'test_data')

class BettyTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        image_root = tempfile.mkdtemp()
        app.config['BETTY'] = {
            'DATABASE': 'sqlite://',
            'IMAGE_ROOT': image_root,
            'RATIOS': (
                "1x1",
                "2x1",
                "3x1",
                "3x4",
                "4x3",
                "16x9"
            )
        }
        self.client = app.test_client()
        init_db()

    def test_image_upload(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            res = self.client.post('/api/new', data=dict(
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
        headers = [('Content-Type', 'application/json')]

        res = self.client.post('/api/%s/1x1' % image.id, headers=headers, data=json.dumps(new_selection))
        assert res.status_code == 200

        db_session.refresh(image, ['selections'])
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

        res = self.client.get('/api/%s' % image.id)
        assert res.status_code == 200

        headers = [('Content-Type', 'application/json')]
        res = self.client.patch('/api/%s' % image.id, headers=headers, data=json.dumps({'name': 'Updated'}))
        assert res.status_code == 200
        db_session.refresh(image)
        assert image.name == 'Updated'

    def test_image_search(self):
        image = Image(name="BLERGH", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        res = self.client.get('/api/search?q=blergh')
        assert res.status_code == 200

    def tearDown(self):
        os.close(self.db_fd)
        # os.unlink(app.config['BETTY']['DATABASE'])
        shutil.rmtree(app.config['BETTY']['IMAGE_ROOT'])


if __name__ == '__main__':
    unittest.main()
