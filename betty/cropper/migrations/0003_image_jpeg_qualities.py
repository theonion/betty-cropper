# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cropper', '0002_auto_20141203_2115'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='jpeg_quality_settings',
            field=jsonfield.fields.JSONField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
