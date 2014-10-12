# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import betty.authtoken.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('public_token', models.CharField(default=betty.authtoken.models.random_token, unique=True, max_length=255)),
                ('private_token', models.CharField(default=betty.authtoken.models.random_token, max_length=255)),
                ('image_read_permission', models.BooleanField(default=False)),
                ('image_change_permission', models.BooleanField(default=False)),
                ('image_crop_permission', models.BooleanField(default=False)),
                ('image_add_permsission', models.BooleanField(default=False)),
                ('image_delete_permission', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
