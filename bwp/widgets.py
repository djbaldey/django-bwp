# -*- coding: utf-8 -*-
#
#  bwp/widgets.py
#
#  Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import unicode_literals

from copy import deepcopy

from django.db import models
from django.db.models.fields import AutoField
from django.utils.encoding import force_text, python_2_unicode_compatible

from quickapi.http import tojson

from bwp.db import fields as bwp_fields


@python_2_unicode_compatible
class GeneralWidget(object):
    field = None
    is_configured = False
    is_required = False
    is_editable = True
    is_hidden = False
    tag = None
    attr = None

    def __init__(self, force_visible=False, **kwargs):
        for key, val in kwargs.items():
            self.__dict__[key] = val
        if isinstance(self.field, AutoField):
            self.is_hidden = True
        if self.attr is None:
            self.attr = {}
        if force_visible:
            self.is_hidden = False

    def __str__(self):
        dic = self.get_dict()
        return tojson(dic)

    def get_dict(self):
        d = {
            'name': self.field.name,
            'hidden': self.is_hidden,
            'tag': self.tag,
            'attr': self.attr,
            'model': force_text(self.field.model._meta),
            'choices': None,
            # 'djangofield': self.field.get_internal_type()
        }

        if self.field.related_model:
            opts = self.field.related_model._meta
            d['model'] = str(opts)
            if hasattr(self.field, 'verbose_name'):
                d['label'] = force_text(self.field.verbose_name)
            else:
                d['label'] = force_text(opts.verbose_name)
        else:
            d['label'] = force_text(self.field.verbose_name)

        if hasattr(self.field, 'choices') and self.field.choices:
            d['choices'] = self.field.choices
        if hasattr(self.field, 'help_text'):
            d['help_text'] = self.field.help_text

        if hasattr(self, 'select_multiple') and 'multiple' not in self.attr:
            d['attr']['multiple'] = self.select_multiple
        if hasattr(self, 'input_type') and 'type' not in self.attr:
            d['attr']['type'] = self.input_type

        if not self.field.editable:
            d['attr']['disabled'] = True
        if not getattr(self.field, 'blank', False):
            d['attr']['required'] = True
        if d['name'] in ['password', 'passwd']:
            d['attr']['type'] = 'password'
            d['attr']['required'] = False
        if self.is_hidden:
            d['attr']['type'] = 'hidden'

        return d


class SelectWidget(GeneralWidget):
    tag = 'select'


class SelectMultipleWidget(SelectWidget):
    select_multiple = True


class TextWidget(GeneralWidget):
    tag = 'textarea'


class InputWidget(GeneralWidget):
    tag = 'input'
    input_type = 'text'


class IntegerWidget(InputWidget):
    input_type = 'number'


class AutoWidget(IntegerWidget):
    is_hidden = True


class PasswordWidget(InputWidget):
    input_type = 'password'


class CheckboxWidget(InputWidget):
    input_type = 'checkbox'


class EmailWidget(InputWidget):
    input_type = 'email'


class FileWidget(InputWidget):
    input_type = 'file'


class ImageWidget(InputWidget):
    input_type = 'image'


class URLWidget(InputWidget):
    input_type = 'url'


class TimeWidget(InputWidget):
    input_type = 'time'


class DateWidget(InputWidget):
    input_type = 'date'


class DateTimeWidget(InputWidget):
    input_type = 'datetime-local'


class MonthWidget(InputWidget):
    input_type = 'month'


class WeekWidget(InputWidget):
    input_type = 'week'


class TelWidget(InputWidget):
    input_type = 'tel'


class ColorWidget(InputWidget):
    input_type = 'color'


WIDGETS_FOR_DBFIELD = {
    models.ForeignKey: (SelectWidget, None),
    models.ManyToManyField: (SelectMultipleWidget, None),
    models.OneToOneField: (SelectWidget, None),
    models.AutoField: (AutoWidget, {'class': 'integerfield'}),
    models.BigIntegerField: (IntegerWidget, {'class': 'bigintegerfield'}),
    models.BooleanField: (CheckboxWidget, None),
    models.CharField: (InputWidget, None),
    models.CommaSeparatedIntegerField: (InputWidget, None),
    models.DateField: (DateWidget, {'class': 'datefield'}),
    models.DateTimeField: (DateTimeWidget, {'class': 'datetimefield'}),
    models.DecimalField: (InputWidget, {'class': 'decimalfield'}),
    models.EmailField: (EmailWidget, None),
    models.FileField: (FileWidget, None),
    models.FilePathField: (InputWidget, {'class': 'filepathfield'}),
    models.FloatField: (InputWidget, {'class': 'floatfield'}),
    models.ImageField: (ImageWidget, None),
    models.IntegerField: (IntegerWidget, {'class': 'integerfield'}),
    models.IPAddressField: (InputWidget, {'class': 'ipaddressfield'}),
    models.GenericIPAddressField: (InputWidget, {'class': 'ipaddressfield'}),
    models.NullBooleanField: (CheckboxWidget, {'class': 'nullbooleanfield'}),
    models.PositiveIntegerField: (IntegerWidget, {'class': 'positiveintegerfield'}),
    models.PositiveSmallIntegerField: (IntegerWidget, {'class': 'positivesmallintegerfield'}),
    models.SlugField: (InputWidget, {'class': 'slugfield'}),
    models.SmallIntegerField: (IntegerWidget, {'class': 'smallintegerfield'}),
    models.TextField: (TextWidget, {'class': 'textfield', "rows": "3"}),
    models.TimeField: (TimeWidget, {'class': 'timefield'}),
    models.URLField: (URLWidget, None),
    bwp_fields.JSONField: (TextWidget, {'class': 'textfield', "rows": "3"}),
}


def get_widget_from_field(field, force_visible=False):

    def find_class(field):
        for klass in field.__class__.__mro__:
            if klass in WIDGETS_FOR_DBFIELD:
                return WIDGETS_FOR_DBFIELD[klass]
        return (InputWidget, None)

    widget_class, attr = find_class(field)
    if attr is None:
        attr = {}
    else:
        attr = deepcopy(attr)
    # Return instance
    return widget_class(field=field, attr=attr, force_visible=force_visible)
