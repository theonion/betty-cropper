import shutil

import pytest
from logan.runner import configure_app


configure_app(
    project="betty",
    default_settings="betty.conf.server",
    config_path="./tests/betty.testconf.py"
)


@pytest.fixture()
def clean_image_root(request):
    from betty.conf.app import settings
    shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
