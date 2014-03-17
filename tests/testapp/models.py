from django.db import models

from betty.client.fields import ImageField


class TestModel(models.Model):

    image_caption = models.CharField(max_length=255)
    image_alt = models.CharField(max_length=255)

    image = ImageField(alt_field="image_alt", caption_field="image_caption")
