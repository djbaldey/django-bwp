# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import bwp.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('driver', models.CharField(max_length=255, verbose_name='driver', choices=[(b'ICP DAS I-7000/M-7000 DIO', b'ICP DAS I-7000/M-7000 DIO'), (b'Zonerich TCP/IP Printer', b'Zonerich TCP/IP Printer'), (b'Shtrih-M Fiscal Register', b'Shtrih-M Fiscal Register')])),
                ('username', models.CharField(max_length=100, verbose_name='username', blank=True)),
                ('password', models.CharField(max_length=100, verbose_name='password', blank=True)),
                ('port', models.CharField(max_length=50, verbose_name='port', blank=True)),
                ('config', bwp.db.fields.JSONField(default={}, verbose_name='config', blank=True)),
                ('admin_password', models.CharField(max_length=100, verbose_name='admin password', blank=True)),
                ('admin_groups', models.ManyToManyField(related_name='admin_group_localdevice_set', verbose_name='admin groups', to='auth.Group', blank=True)),
                ('admin_users', models.ManyToManyField(related_name='admin_user_localdevice_set', verbose_name='admin users', to=settings.AUTH_USER_MODEL, blank=True)),
                ('groups', models.ManyToManyField(related_name='group_localdevice_set', verbose_name='groups', to='auth.Group', blank=True)),
                ('users', models.ManyToManyField(related_name='user_localdevice_set', verbose_name='users', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'local device',
                'verbose_name_plural': 'local devices',
            },
        ),
        migrations.CreateModel(
            name='RemoteDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('driver', models.CharField(max_length=255, verbose_name='driver', choices=[(b'ICP DAS I-7000/M-7000 DIO', b'ICP DAS I-7000/M-7000 DIO'), (b'Zonerich TCP/IP Printer', b'Zonerich TCP/IP Printer'), (b'Shtrih-M Fiscal Register', b'Shtrih-M Fiscal Register')])),
                ('username', models.CharField(max_length=100, verbose_name='username', blank=True)),
                ('password', models.CharField(max_length=100, verbose_name='password', blank=True)),
                ('remote_url', models.CharField(max_length=200, verbose_name='url')),
                ('remote_id', models.IntegerField(verbose_name='identifier')),
                ('cookies', models.TextField(verbose_name='cookies', blank=True)),
                ('admin_groups', models.ManyToManyField(related_name='admin_group_remotedevice_set', verbose_name='admin groups', to='auth.Group', blank=True)),
                ('admin_users', models.ManyToManyField(related_name='admin_user_remotedevice_set', verbose_name='admin users', to=settings.AUTH_USER_MODEL, blank=True)),
                ('groups', models.ManyToManyField(related_name='group_remotedevice_set', verbose_name='groups', to='auth.Group', blank=True)),
                ('users', models.ManyToManyField(related_name='user_remotedevice_set', verbose_name='users', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'remote device',
                'verbose_name_plural': 'remote devices',
            },
        ),
        migrations.CreateModel(
            name='SpoolerDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='updated')),
                ('state', models.IntegerField(default=1, verbose_name='state', choices=[(1, 'waiting'), (2, 'error')])),
                ('method', models.CharField(max_length=50, verbose_name='method')),
                ('kwargs', bwp.db.fields.JSONField(default={}, verbose_name='config', blank=True)),
                ('group_hash', models.CharField(max_length=32, verbose_name='method', blank=True)),
                ('local_device', models.ForeignKey(verbose_name='local device', to='devices.LocalDevice')),
            ],
            options={
                'ordering': ['pk'],
                'verbose_name': 'spooler device',
                'verbose_name_plural': 'spooler device',
            },
        ),
        migrations.AlterUniqueTogether(
            name='remotedevice',
            unique_together=set([('remote_url', 'remote_id')]),
        ),
    ]
