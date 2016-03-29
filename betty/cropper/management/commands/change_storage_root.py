from django.core.management.base import BaseCommand

from betty.cropper.models import Image


class Command(BaseCommand):
    help = 'Change root path for Image file fields'

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Dry-run (read-only) check mode')
        parser.add_argument('--old', required=True, help='Old root path (ex: /var/betty-cropper)')
        parser.add_argument('--new', required=True, help='New root path (ex: /testing/)')

    def handle(self, *args, **options):
        # Sanity check: Make sure same separator ending
        assert options['old'].endswith('/') == options['new'].endswith('/')

        for image in Image.objects.iterator():

            for field in [image.source,
                          image.optimized]:
                if field:
                    if (field.name.startswith(options['old']) and
                            not field.name.startswith(options['new'])):  # Prevent re-migrating

                        name = (options['new'] + field.name[len(options['old']):])
                        self.stdout.write('{}Update name: {} --> {}'.format(
                            '[CHECK] ' if options['check'] else '',
                            field.name,
                            name))

                        if not options['check']:
                            field.name = name
                            image.save()
