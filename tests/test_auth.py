import os

from django.test import TestCase, Client
from django.contrib.auth import get_user_model, authenticate
User = get_user_model()


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class UserTestCase(TestCase):

    def test_user_creation(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="tech@theonion.com",
            password="testing123"
        )
        self.assertTrue(admin.api_key is not None)

    def test_authentication_backend(self):
        password = User.objects.make_random_password()
        admin = User.objects.create_superuser(
            username="admin",
            email="tech@theonion.com",
            password=password
        )
        self.assertEqual(admin, authenticate(username="admin", password=password))
        self.assertEqual(admin, authenticate(api_key=admin.api_key))

    def test_search_api(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="tech@theonion.com",
            password="whatevs"
        )
        client = Client()
        self.assertTrue(client.login(api_key=admin.api_key))
        response = client.get("/images/api/search?q=testing")
        self.assertTrue(response.status_code, 200)
