#!/usr/bin/env python
import tempfile

import django
from django.conf import settings
import os.path
import sys
import os

from betty.conf import server as betty_server_settings

# from betty.flask.tests import CroppingTestCase, APITestCase

# Detect location and available modules
module_root = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':

    # Run the Flask suite
    # cropping_suite = unittest.TestLoader().loadTestsFromTestCase(CroppingTestCase)
    # api_suite = unittest.TestLoader().loadTestsFromTestCase(APITestCase)
    # flask_suite = unittest.TestSuite([cropping_suite, api_suite])
    # unittest.TextTestRunner(verbosity=2).run(flask_suite)

    settings.configure(
        betty_server_settings,
        MEDIA_ROOT=tempfile.mkdtemp("bettycropper"),
        TEMPLATE_DIRS=(os.path.join(module_root, 'tests', 'templates'), ),
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
    failures = runner.run_tests(['betty'])

    if failures:
        sys.exit(bool(failures))
