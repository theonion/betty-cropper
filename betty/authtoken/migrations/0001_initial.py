# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ApiToken'
        db.create_table(u'authtoken_apitoken', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('public_token', self.gf('django.db.models.fields.CharField')(default='4cb80f9c7eab0a4068bc07b6624be59a111a96d0', unique=True, max_length=255)),
            ('private_token', self.gf('django.db.models.fields.CharField')(default='ef982e492813b9261f2eefd00e0a2cbec7a25804', max_length=255)),
            ('image_read_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_change_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_crop_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_add_permsission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image_delete_permission', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'authtoken', ['ApiToken'])


    def backwards(self, orm):
        # Deleting model 'ApiToken'
        db.delete_table(u'authtoken_apitoken')


    models = {
        u'authtoken.apitoken': {
            'Meta': {'object_name': 'ApiToken'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_add_permsission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_change_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_crop_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_delete_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image_read_permission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'private_token': ('django.db.models.fields.CharField', [], {'default': "'1be13be5255cd0f21e0bd3b93e822944e149d0ce'", 'max_length': '255'}),
            'public_token': ('django.db.models.fields.CharField', [], {'default': "'6745892100387ff2df7416c39777749d1f72549f'", 'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['authtoken']