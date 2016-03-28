# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import betty.cropper.models


class Migration(migrations.Migration):

    replaces = [('cropper', '0001_initial'), ('cropper', '0002_auto_20141203_2115'), ('cropper', '0003_image_jpeg_qualities'), ('cropper', '0004_auto_20160317_1706')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255)),
                ('credit', models.CharField(null=True, blank=True, max_length=120)),
                ('source', models.FileField(upload_to=betty.cropper.models.source_upload_to, null=True, blank=True, max_length=255)),
                ('optimized', models.FileField(upload_to=betty.cropper.models.optimized_upload_to, null=True, blank=True, max_length=255)),
                ('height', models.IntegerField(null=True, blank=True)),
                ('width', models.IntegerField(null=True, blank=True)),
                ('selections', jsonfield.fields.JSONField(null=True, blank=True)),
                ('jpeg_quality', models.IntegerField(null=True, blank=True)),
                ('animated', models.BooleanField(default=False)),
                ('jpeg_quality_settings', jsonfield.fields.JSONField(null=True, blank=True)),
            ],
            options={
                'permissions': (('read', 'Can search images, and see the detail data'), ('crop', 'Can crop images')),
            },
        ),
    ]
