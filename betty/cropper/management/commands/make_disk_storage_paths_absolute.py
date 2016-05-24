from optparse import make_option
import os.path

from betty.conf.app import settings
from django.core.management.base import BaseCommand

from betty.cropper.models import Image


class Command(BaseCommand):
    help = 'Convert disk storage relative paths to absolute'

    # This needs to run on Django 1.7
    option_list = BaseCommand.option_list + (
        make_option('--check',
                    action='store_true',
                    dest='check',
                    default=False,
                    help='Dry-run (read-only) check mode'),
        make_option('--limit',
                    type=int,
                    dest='limit',
                    help='Maximum number of images to process'),
    )

    def handle(self, *args, **options):

        for idx, image in enumerate(Image.objects.order_by('pk').iterator()):

            if options['limit'] and idx >= options['limit']:
                self.stdout.write('Early exit (limit %s reached)'.format(options['limit']))
                break

            for field in [image.source,
                          image.optimized]:

                if field.name:
                    if not field.name.startswith(settings.MEDIA_ROOT):

                        path = os.path.join(settings.MEDIA_ROOT, field.name)

                        self.stdout.write(u'{}{}\t{} --> {}'.format(
                            '[CHECK] ' if options['check'] else '',
                            image.id,
                            field.name,
                            path))

                        # Sanity checks
                        assert os.path.exists(path)
                        assert path.startswith(settings.MEDIA_ROOT)
                        assert path.endswith(field.name)
                        assert '//' not in path, "Guard against weird path joins"

                        if not options['check']:
                            field.name = path
                            image.save()
                    else:
                        self.stdout.write('SKIP: {} {}'.format(image.id, field.name))
