# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Image.source'
        db.alter_column(u'cropper_image', 'source', self.gf('django.db.models.fields.files.FileField')(max_length=255))

    def backwards(self, orm):

        # Changing field 'Image.source'
        db.alter_column(u'cropper_image', 'source', self.gf('django.db.models.fields.files.FileField')(max_length=100))

    models = {
        u'cropper.image': {
            'Meta': {'object_name': 'Image'},
            'credit': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'selections': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['cropper']