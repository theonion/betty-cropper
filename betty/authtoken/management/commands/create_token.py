from django.core.management.base import BaseCommand, CommandError
from betty.authtoken.models import ApiToken


class Command(BaseCommand):
    args = '<public_token> <private_token>'
    help = 'Creates an API Token pair'

    def handle(self, *args, **options):

        if len(args) == 2:
            token = ApiToken.objects.create(
                public_token=args[0],
                private_token=args[1],
                image_read_permission=True,
                image_change_permission=True,
                image_crop_permission=True,
                image_add_permsission=True,
                image_delete_permission=True
            )
        elif len(args) == 0:
            token = ApiToken.objects.create_superuser()
        else:
            raise CommandError("Usage: django-admin.py create_token <public_token> <private_token>")

        self.stdout.write("Public token: {0}\n".format(token.public_token))
        self.stdout.write("Private token: {0}\n".format(token.private_token))
