# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.files.storage
import betty.cropper.models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('credit', models.CharField(max_length=120, null=True, blank=True)),
                ('source', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url='/', location='/private/var/folders/_3/mlzyzxsj5lb617stmlnstkgr0000gp/T/virtualenv.xyQsXv9C/images'), max_length=255, null=True, upload_to=betty.cropper.models.source_upload_to, blank=True)),
                ('optimized', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url='/', location='/private/var/folders/_3/mlzyzxsj5lb617stmlnstkgr0000gp/T/virtualenv.xyQsXv9C/images'), max_length=255, null=True, upload_to=betty.cropper.models.optimized_upload_to, blank=True)),
                ('height', models.IntegerField(null=True, blank=True)),
                ('width', models.IntegerField(null=True, blank=True)),
                ('selections', jsonfield.fields.JSONField(null=True, blank=True)),
                ('jpeg_quality', models.IntegerField(null=True, blank=True)),
                ('animated', models.BooleanField(default=False)),
            ],
            options={
                'permissions': (('read', 'Can search images, and see the detail data'), ('crop', 'Can crop images')),
            },
            bases=(models.Model,),
        ),
    ]
