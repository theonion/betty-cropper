import os

from django.test import TestCase, Client

from betty.api.models import ApiToken


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class AuthTestCase(TestCase):

    def test_user_creation(self):
        token = ApiToken.objects.create_standard_user()
        self.assertTrue(token.public_token is not None)
        self.assertTrue(token.private_token is not None)

    def test_search_api(self):
        token = ApiToken.objects.create_standard_user()
        client = Client()
        response = client.get(
            "/images/api/search?q=testing",
            HTTP_X_BETTY_API_KEY=token.public_token)
        self.assertEquals(response.status_code, 200)
