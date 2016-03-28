# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import betty.cropper.models


class Migration(migrations.Migration):

    dependencies = [
        ('cropper', '0003_image_jpeg_qualities'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='optimized',
            field=models.FileField(null=True, blank=True, max_length=255, upload_to=betty.cropper.models.optimized_upload_to),
        ),
        migrations.AlterField(
            model_name='image',
            name='source',
            field=models.FileField(null=True, blank=True, max_length=255, upload_to=betty.cropper.models.source_upload_to),
        ),
    ]
