from django.db import models

from betty.core import BettyImageMixin
from betty.django.conf import settings

class Image(models.Model, BettyImageMixin):

    @classmethod
    def get_settings(cls):
        return settings.BETTY_CROPPER