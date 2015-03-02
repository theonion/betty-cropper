import django
from django.core import management
from django.core.management.base import CommandError
from betty.authtoken.models import ApiToken

import pytest


@pytest.mark.django_db
def test_create_token():
    token_count = ApiToken.objects.count()
    management.call_command("create_token")
    assert ApiToken.objects.count() == (token_count + 1)


@pytest.mark.django_db
def test_create_specific_token():
    management.call_command("create_token", "noop", "noop")
    qs = ApiToken.objects.filter(private_token="noop", public_token="noop")
    assert qs.count() == 1


def test_command_error():
    if django.VERSION[1] > 4:
        with pytest.raises(CommandError):
            management.call_command("create_token", "noop")

        with pytest.raises(CommandError):
            management.call_command("create_token", "noop", "noop", "noop")
