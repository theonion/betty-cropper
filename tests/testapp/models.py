from django.db import models

from betty.client.fields import ImageField


class TestModel(models.Model):
    image = ImageField()
