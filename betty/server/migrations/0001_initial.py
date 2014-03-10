# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ApiToken'
        db.create_table(u'server_apitoken', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('public_token', self.gf('django.db.models.fields.CharField')(default='3cec66b421610c200ef0699a3187d310a554619e', unique=True, max_length=255)),
            ('private_token', self.gf('django.db.models.fields.CharField')(default='8b2e7dcaade07021afdea35e97fe87713377ae5e', max_length=255)),
            ('image_read_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_change_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_crop_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_add_permsission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_delete_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'server', ['ApiToken'])

        # Adding model 'Image'
        db.create_table(u'server_image', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('credit', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('selections', self.gf('jsonfield.fields.JSONField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'server', ['Image'])


    def backwards(self, orm):
        # Deleting model 'ApiToken'
        db.delete_table(u'server_apitoken')

        # Deleting model 'Image'
        db.delete_table(u'server_image')


    models = {
        u'server.apitoken': {
            'Meta': {'object_name': 'ApiToken'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_add_permsission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_change_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_crop_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_delete_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_read_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'private_token': ('django.db.models.fields.CharField', [], {'default': "'072d2a6aaa92fa01d903fee4b209781445c3c6a2'", 'max_length': '255'}),
            'public_token': ('django.db.models.fields.CharField', [], {'default': "'7bd9677b5c89f1017b48a0e3e225a5eed36e28bc'", 'unique': 'True', 'max_length': '255'})
        },
        u'server.image': {
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

    complete_apps = ['server']