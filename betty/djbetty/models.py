import os

from django.db import models

from betty.core import BettyImageMixin
from betty.djbetty.conf import settings

def upload_to(instance, filename):
    return os.path.join(instance.path(), filename)

class Image(models.Model, BettyImageMixin):

    source = models.FileField(upload_to=upload_to)
    height = models.IntegerField()
    width = models.IntegerField()
    credit = models.CharField(max_length=120)
    selections = models.TextField()

    @classmethod
    def get_settings(cls):
        return settings.BETTY_CROPPER