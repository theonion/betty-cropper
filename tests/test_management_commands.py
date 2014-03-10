import io

from django.core import management
from django.core.management.base import CommandError
from django.test import TestCase
from betty.server.auth import ApiToken


class CreateTokenTestCase(TestCase):

    def test_create_token(self):
        with io.BytesIO() as f:
            management.call_command("create_token", stdout=f)
            self.assertEqual(ApiToken.objects.count(), 1)

            self.assertTrue("Public token: " in f.getvalue())
            self.assertTrue("Private token: " in f.getvalue())

    def test_create_specific_token(self):
        with io.BytesIO() as f:
            management.call_command("create_token", "noop", "noop", stdout=f)
            self.assertEqual(ApiToken.objects.count(), 1)

            self.assertEquals("Public token: noop\nPrivate token: noop\n", f.getvalue())

    def test_command_error(self):
        with self.assertRaises(CommandError):
            management.call_command("create_token", "noop")

        with self.assertRaises(CommandError):
            management.call_command("create_token", "noop", "noop", "noop")
