# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Image.optimized'
        db.add_column(u'cropper_image', 'optimized',
                      self.gf('django.db.models.fields.files.FileField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Image.jpeg_quality'
        db.add_column(u'cropper_image', 'jpeg_quality',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Image.animated'
        db.add_column(u'cropper_image', 'animated',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Image.optimized'
        db.delete_column(u'cropper_image', 'optimized')

        # Deleting field 'Image.jpeg_quality'
        db.delete_column(u'cropper_image', 'jpeg_quality')

        # Deleting field 'Image.animated'
        db.delete_column(u'cropper_image', 'animated')


    models = {
        u'cropper.image': {
            'Meta': {'object_name': 'Image'},
            'animated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'credit': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jpeg_quality': ('django.db.models.fields.IntegerField', [], {'default': '80'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'optimized': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'selections': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['cropper']