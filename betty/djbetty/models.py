import os

from django.db import models

from betty.core import BettyImageMixin
from .conf import settings
from .fields import JSONField

def upload_to(instance, filename):
    return os.path.join(instance.path(), filename)

class Image(models.Model, BettyImageMixin):

    source = models.FileField(upload_to=upload_to)
    name = models.CharField(max_length=255)
    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    credit = models.CharField(max_length=120)
    selections = JSONField(null=True, blank=True)

    @classmethod
    def get_settings(cls):
        return settings.BETTY_CROPPER

    def src_path(self):
        return self.source.path