# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cropper', '0001_squashed_0004_auto_20160317_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='last_modified',
            field=models.DateTimeField(default=timezone.now(), auto_now=True),
            preserve_default=False,
        ),
    ]
