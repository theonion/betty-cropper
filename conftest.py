import os
import tempfile

from django.conf import settings

from betty.conf import server

MODULE_ROOT = os.path.dirname(os.path.realpath(__file__))


def pytest_configure():
    settings.configure(
        server,
        BETTY_DEFAULT_IMAGE=666,
        BETTY_IMAGE_URL="http://localhost:8081/images/",
        MEDIA_ROOT=tempfile.mkdtemp("bettycropper"),
        TEMPLATE_DIRS=(os.path.join(MODULE_ROOT, 'tests', 'templates'),),
        INSTALLED_APPS=server.INSTALLED_APPS + ("tests.testapp",),
        BETTY_WIDTHS=(80, 150, 240, 300, 320, 400, 480, 620, 640, 820, 960, 1200, 1600),
    )
