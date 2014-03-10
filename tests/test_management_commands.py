import io

import django
from django.core import management
from django.core.management.base import CommandError
from django.test import TestCase
from betty.server.auth import ApiToken


class CreateTokenTestCase(TestCase):

    def test_create_token(self):
        management.call_command("create_token")
        self.assertEqual(ApiToken.objects.count(), 1)

    def test_create_specific_token(self):
        management.call_command("create_token", "noop", "noop")
        self.assertEqual(ApiToken.objects.count(), 1)
        self.assertEqual(ApiToken.objects.filter(private_token="noop", public_token="noop").count(), 1)

    def test_command_error(self):
        if django.VERSION[1] > 4:
            with self.assertRaises(CommandError):
                management.call_command("create_token", "noop")

            with self.assertRaises(CommandError):
                management.call_command("create_token", "noop", "noop", "noop")
