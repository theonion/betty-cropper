from optparse import make_option

from django.core.management.base import BaseCommand

from betty.cropper.models import Image


class Command(BaseCommand):
    help = 'Change root path for Image file fields'

    # This needs to run on Django 1.7
    option_list = BaseCommand.option_list + (
        make_option('--check',
                    action='store_true',
                    dest='check',
                    default=False,
                    help='Dry-run (read-only) check mode'),
        make_option('--old',
                    dest='old',
                    help='Old root path (ex: /var/betty-cropper/)'),
        make_option('--new',
                    dest='new',
                    help='New root path (ex: /testing/)'),
    )

    # This only works on Django 1.8+
    # def add_arguments(self, parser):
    #     parser.add_argument('--check', action='store_true', help='')
    #     parser.add_argument('--old', required=True, help='Old root path (ex: /var/betty-cropper)')
    #     parser.add_argument('--new', required=True, help='New root path (ex: /testing/)')

    def handle(self, *args, **options):

        if not options['old']:
            raise Exception('Old root not provided')

        if not options['new']:
            raise Exception('New root not provided')

        # Sanity check: Make sure same separator ending
        assert options['old'].endswith('/') == options['new'].endswith('/')

        self.stdout.write('Checking {} images...'.format(Image.objects.count()))

        for image in Image.objects.iterator():

            for field in [image.source,
                          image.optimized]:
                if field:
                    if (field.name.startswith(options['old']) and
                            not field.name.startswith(options['new'])):  # Prevent re-migrating

                        name = (options['new'] + field.name[len(options['old']):])
                        self.stdout.write(u'{}Update name: {} --> {}'.format(
                            '[CHECK] ' if options['check'] else '',
                            field.name,
                            name))

                        if not options['check']:
                            field.name = name
                            image.save()
