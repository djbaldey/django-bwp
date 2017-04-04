# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import bwp.utils.classes


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('qualifiers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('bound', models.IntegerField(default=1, verbose_name='bound', choices=[(1, 'object'), (2, 'model')])),
                ('template_name', models.CharField(max_length=255, verbose_name='HTML template name')),
                ('format_out', models.CharField(default=b'html', max_length=4, verbose_name='format out', choices=[(b'html', 'HTML page'), (b'txt', 'plain text'), (b'odt', 'text document (ODT)'), (b'ods', 'spreadsheet (ODS)')])),
                ('content_type', models.ForeignKey(verbose_name='content type', to='contenttypes.ContentType')),
                ('qualifier', models.ForeignKey(related_name='reports_document_set', verbose_name='qualifier', blank=True, to='qualifiers.Document', null=True)),
            ],
            options={
                'ordering': ['qualifier', 'title'],
                'verbose_name': 'document',
                'verbose_name_plural': 'documents',
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255, verbose_name='label', blank=True)),
                ('file', models.FileField(upload_to=bwp.utils.classes.upload_to, max_length=260, verbose_name='file')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('document', models.ForeignKey(editable=False, to='reports.Document', verbose_name='document')),
                ('user', models.ForeignKey(blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='user')),
            ],
            options={
                'ordering': ['-created'],
                'verbose_name': 'generated report',
                'verbose_name_plural': 'generated reports',
            },
        ),
    ]
