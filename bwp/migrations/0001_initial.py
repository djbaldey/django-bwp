# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import bwp.db.fields
import bwp.utils.classes


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalUserSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json', bwp.db.fields.JSONField(verbose_name='JSON value', blank=True)),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user'],
                'verbose_name': 'global settings',
                'verbose_name_plural': 'global settings',
            },
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_time', models.DateTimeField(auto_now=True, verbose_name='action time')),
                ('object_id', models.TextField(null=True, verbose_name='object id', blank=True)),
                ('object_repr', models.CharField(max_length=200, verbose_name='object repr')),
                ('action_flag', models.PositiveSmallIntegerField(verbose_name='action flag')),
                ('change_message', models.TextField(verbose_name='change message', blank=True)),
                ('content_type', models.ForeignKey(related_name='bwp_log_set', blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(related_name='bwp_log_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-action_time',),
                'db_table': 'bwp_log',
                'verbose_name': 'log entry',
                'verbose_name_plural': 'log entries',
            },
        ),
        migrations.CreateModel(
            name='PermissionRead',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hidden', models.BooleanField(default=False, verbose_name='as hidden')),
                ('content_type', models.ForeignKey(verbose_name='content type', blank=True, to='contenttypes.ContentType', null=True)),
                ('groups', models.ManyToManyField(to='auth.Group', verbose_name='groups', blank=True)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='users', blank=True)),
            ],
            options={
                'ordering': ('content_type',),
                'verbose_name': 'permission read',
                'verbose_name_plural': 'permissions read',
            },
        ),
        migrations.CreateModel(
            name='TempUploadFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(upload_to=bwp.utils.classes.upload_to, verbose_name='file')),
                ('user', models.ForeignKey(verbose_name='user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created',),
                'verbose_name': 'temporarily upload file',
                'verbose_name_plural': 'temporarily upload files',
            },
        ),
        migrations.AlterUniqueTogether(
            name='globalusersettings',
            unique_together=set([('user',)]),
        ),
    ]
