# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import betty.cropper.models
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('cropper', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='optimized',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url='/', location='/Users/csinchok/Development/betty-cropper/images'), max_length=255, null=True, upload_to=betty.cropper.models.optimized_upload_to, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='image',
            name='source',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url='/', location='/Users/csinchok/Development/betty-cropper/images'), max_length=255, null=True, upload_to=betty.cropper.models.source_upload_to, blank=True),
            preserve_default=True,
        ),
    ]
