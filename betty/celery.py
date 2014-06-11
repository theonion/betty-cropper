from __future__ import absolute_import

from betty.cropper.utils import runner
from celery import Celery
from django.conf import settings

app = Celery('betty')

try:
    runner.configure()
except:
    pass

app.config_from_object(settings)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
