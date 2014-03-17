# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Image'
        db.create_table(u'cropper_image', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('credit', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('selections', self.gf('jsonfield.fields.JSONField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'cropper', ['Image'])


    def backwards(self, orm):
        # Deleting model 'Image'
        db.delete_table(u'cropper_image')


    models = {
        u'cropper.image': {
            'Meta': {'object_name': 'Image'},
            'credit': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'selections': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['cropper']