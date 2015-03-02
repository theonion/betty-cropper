import os
import pytest

from django.test import Client

from betty.authtoken.models import ApiToken


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.mark.django_db
def test_user_creation(client):
    token = ApiToken.objects.create_standard_user()
    assert token.public_token is not None
    assert token.private_token is not None


@pytest.mark.django_db
def test_search_api(client):
    token = ApiToken.objects.create_standard_user()
    client = Client()
    response = client.get(
        "/images/api/search?q=testing",
        HTTP_X_BETTY_API_KEY=token.public_token)
    assert response.status_code == 200
