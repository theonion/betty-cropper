#!/usr/bin/env python
import unittest

import django
from django.conf import settings, global_settings as default_settings
import os.path
import sys
import os

from betty.flask.tests import CroppingTestCase, APITestCase

# Detect location and available modules
module_root = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':

    # Run the Flask suite
    cropping_suite = unittest.TestLoader().loadTestsFromTestCase(CroppingTestCase)
    api_suite = unittest.TestLoader().loadTestsFromTestCase(APITestCase)
    flask_suite = unittest.TestSuite([cropping_suite, api_suite])
    unittest.TextTestRunner(verbosity=2).run(flask_suite)

    settings.configure(
        DEBUG = False,  # will be False anyway by DjangoTestRunner.
        TEMPLATE_DEBUG = False,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        TEMPLATE_DIRS = (os.path.join(module_root, 'tests', 'templates'), ),
        TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader'
        ),
        TEMPLATE_CONTEXT_PROCESSORS = default_settings.TEMPLATE_CONTEXT_PROCESSORS + (
            'django.core.context_processors.request',
        ),
        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',

            'betty.djbetty',
        ),
        SITE_ID = 3,

        ROOT_URLCONF = 'tests.urls',
    )

    if django.VERSION[1] < 6:
        settings.INSTALLED_APPS += ('discover_runner',)
        # settings.TEST_RUNNER = 'tests.runner.XMLTestRunner'
        settings.TEST_RUNNER = 'discover_runner.DiscoverRunner'
        settings.TEST_DISCOVER_TOP_LEVEL = os.path.join(module_root, 'bulbs')
        print(settings.TEST_DISCOVER_TOP_LEVEL)

    # ---- app start
    verbosity = 2 if '-v' in sys.argv else 1

    from django.test.utils import get_runner
    TestRunner = get_runner(settings)  # DjangoTestSuiteRunner
    runner = TestRunner(verbosity=verbosity, interactive=True, failfast=False)
    failures = runner.run_tests(['betty.djbetty',])

    if failures:
        sys.exit(bool(failures))
