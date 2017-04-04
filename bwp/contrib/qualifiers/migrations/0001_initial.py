# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('code', models.CharField(max_length=3, serialize=False, verbose_name='code', primary_key=True)),
                ('symbol2', models.CharField(unique=True, max_length=2, verbose_name='code 2 symbol')),
                ('symbol3', models.CharField(unique=True, max_length=3, verbose_name='code 3 symbol')),
                ('full_title', models.CharField(max_length=512, verbose_name='full title', blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'country',
                'verbose_name_plural': 'countries',
            },
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('code', models.CharField(max_length=3, serialize=False, verbose_name='code', primary_key=True)),
                ('symbol3', models.CharField(unique=True, max_length=3, verbose_name='code 3 symbol')),
                ('countries', models.ManyToManyField(to='qualifiers.Country', verbose_name='countries', blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'currency',
                'verbose_name_plural': 'currencies',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('title', models.TextField(verbose_name='title')),
                ('code', models.CharField(max_length=7, serialize=False, verbose_name='code', primary_key=True)),
                ('control', models.SmallIntegerField(null=True, verbose_name='control number', blank=True)),
                ('document_index', models.CharField(max_length=64, null=True, verbose_name='document index', blank=True)),
                ('period', models.CharField(max_length=128, null=True, verbose_name='periodic', blank=True)),
                ('parent', models.ForeignKey(verbose_name='document parent', blank=True, to='qualifiers.Document', null=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'document',
                'verbose_name_plural': 'documents',
            },
        ),
        migrations.CreateModel(
            name='MeasureUnit',
            fields=[
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('code', models.CharField(max_length=3, serialize=False, verbose_name='code', primary_key=True)),
                ('note_ru', models.CharField(help_text='notation RU', max_length=50, null=True, verbose_name='RU', blank=True)),
                ('note_iso', models.CharField(help_text='notation ISO', max_length=50, null=True, verbose_name='ISO', blank=True)),
                ('symbol_ru', models.CharField(help_text='symbolic notation RU', max_length=50, null=True, verbose_name='symbol RU', blank=True)),
                ('symbol_iso', models.CharField(help_text='symbolic notation ISO', max_length=50, null=True, verbose_name='symbol ISO', blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'unit',
                'verbose_name_plural': 'measure units',
            },
        ),
        migrations.CreateModel(
            name='MeasureUnitCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'category',
                'verbose_name_plural': 'categories of measure units',
            },
        ),
        migrations.CreateModel(
            name='MeasureUnitGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'group',
                'verbose_name_plural': 'groups of measure units',
            },
        ),
        migrations.AddField(
            model_name='measureunit',
            name='category',
            field=models.ForeignKey(verbose_name='category', blank=True, to='qualifiers.MeasureUnitCategory', null=True),
        ),
        migrations.AddField(
            model_name='measureunit',
            name='group',
            field=models.ForeignKey(verbose_name='group', blank=True, to='qualifiers.MeasureUnitGroup', null=True),
        ),
    ]
