from django.db import models

from betty.cropped.fields import ImageField


class TestModel(models.Model):

    image_caption = models.CharField(max_length=255)
    image_alt = models.CharField(max_length=255)

    listing_image = ImageField(null=True, blank=True)
    image = ImageField(alt_field="image_alt", caption_field="image_caption", null=True, blank=True)
