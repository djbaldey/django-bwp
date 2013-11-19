# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
###############################################################################
# This file is part of BWP.
#
#    BWP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    BWP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with BWP.  If not, see <http://www.gnu.org/licenses/>.
#
# Этот файл — часть BWP.
#
#   BWP - свободная программа: вы можете перераспространять ее и/или
#   изменять ее на условиях Стандартной общественной лицензии GNU в том виде,
#   в каком она была опубликована Фондом свободного программного обеспечения;
#   либо версии 3 лицензии, либо (по вашему выбору) любой более поздней
#   версии.
#
#   BWP распространяется в надежде, что она будет полезной,
#   но БЕЗО ВСЯКИХ ГАРАНТИЙ; даже без неявной гарантии ТОВАРНОГО ВИДА
#   или ПРИГОДНОСТИ ДЛЯ ОПРЕДЕЛЕННЫХ ЦЕЛЕЙ. Подробнее см. в Стандартной
#   общественной лицензии GNU.
#
#   Вы должны были получить копию Стандартной общественной лицензии GNU
#   вместе с этой программой. Если это не так, см.
#   <http://www.gnu.org/licenses/>.
###############################################################################
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _ 
from django.forms import widgets
from quickapi.http import JSONEncoder
from bwp.utils import print_debug
from bwp.conf import settings 

import os, datetime, json as jsonlib

try:
    from tinymce.models import TinyMCEField
except ImportError:
    from django.db.models import TextField as TinyMCEField

try:
    from unidecode import unidecode
    use_unidecode = True
except ImportError:
    use_unidecode = False

class HTMLField(models.TextField):
    pass

class MarkdownField(models.TextField):
    pass

class PasswordField(models.CharField):
    pass

class JSONField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def contribute_to_class(self, cls, name):
        super(JSONField, self).contribute_to_class(cls, name)

        def get_json(model):
            return self.get_db_prep_value(getattr(model, self.attname))
        setattr(cls, 'get_%s_json' % self.name, get_json)

        def set_json(model, json):
            setattr(model, self.attname, self.to_python(json))
        setattr(cls, 'set_%s_json' % self.name, set_json)

    def formfield(self, **kwargs):
        defaults = {'widget': widgets.Textarea}
        defaults.update(kwargs)
        return super(JSONField, self).formfield(**defaults)

    def get_db_prep_save(self, value, connection, **kwargs):
        """Convert our JSON object to a string before we save"""

        if value == "":
            return None

        if isinstance(value, (list, dict)):
            value = jsonlib.dumps(value, cls=JSONEncoder,
                    ensure_ascii=False,
                    indent=4)
            try:
                value = value.encode('utf-8')
            except:
                pass

        return super(JSONField, self).get_db_prep_save(
                            value, connection=connection, **kwargs)

    def to_python(self, value, **kwargs):
        """Convert our string value to JSON after we load it from the DB"""

        if value == "":
            return None

        if not isinstance(value, basestring):
            return value

        try:
            return jsonlib.loads(value, encoding=settings.DEFAULT_CHARSET)
        except ValueError, e:
            # If string could not parse as JSON it's means that it's Python
            # string saved to JSONField.
            return value

    def _get_val_from_obj(self, obj):
        if obj is not None:
            value = getattr(obj, self.attname)
            return self.get_db_prep_save(value, connection=None)
        else:
            return self.get_db_prep_save(self.get_default(), connection=None)

FIELD_TYPES = {
    models.ForeignKey:                  {'type': 'object'},
    models.ManyToManyField:             {'type': 'object_list'},
    models.OneToOneField:               {'type': 'object'},
    models.AutoField:                   {'type': 'int'},
    models.BigIntegerField:             {'type': 'int', 'min': -9223372036854775808, 'max': 9223372036854775807},
    models.BooleanField:                {'type': 'bool'},
    models.CharField:                   {'type': 'str'},
    models.CommaSeparatedIntegerField:  {'type': 'int_list'},
    models.DateField:                   {'type': 'date', 'format': settings.DATE_FORMAT},
    models.DateTimeField:               {'type': 'datetime', 'format': settings.DATETIME_FORMAT},
    models.DecimalField:                {'type': 'decimal'},
    models.EmailField:                  {'type': 'email'},
    models.FileField:                   {'type': 'file'},
    models.FilePathField:               {'type': 'path'},
    models.FloatField:                  {'type': 'float'},
    models.ImageField:                  {'type': 'image'},
    models.IntegerField:                {'type': 'int'},
    models.IPAddressField:              {'type': 'ip'},
    models.GenericIPAddressField:       {'type': 'ip'},
    models.NullBooleanField:            {'type': 'null_bool'},
    models.PositiveIntegerField:        {'type': 'int', 'min': 0},
    models.PositiveSmallIntegerField:   {'type': 'int', 'min': 0, 'max': 32767},
    models.SlugField:                   {'type': 'str', 'format': '[-\w]+'},
    models.SmallIntegerField:           {'type': 'int', 'min': -32768, 'max': 32767},
    models.TextField:                   {'type': 'text'},
    models.TimeField:                   {'type': 'time', 'format': settings.TIME_FORMAT},
    models.URLField:                    {'type': 'url'},
    HTMLField:                          {'type': 'html'},
    MarkdownField:                      {'type': 'markdown'},
    PasswordField:                      {'type': 'password'},
    JSONField:                          {'type': 'json'},
    TinyMCEField:                       {'type': 'html'},
}

def get_scheme_fields(iterfield):
    if not isinstance(iterfield, (list, tuple)):
        iterfield = [iterfield]

    fields = {}

    for field in iterfield:
        _type = type(field)
        d = FIELD_TYPES.get(_type, {'type': 'str'}).copy()
        d['label'] = field.verbose_name
        if field.choices:
            d['options'] = field.choices
        if field.rel:
            d['placeholder'] = _('Select object')
        if not field.editable:
            d['disabled'] = True
        if field.auto_created:
            d['hidden'] = True
        if not field.blank:
            d['required'] = True
        if field.has_default():
            if isinstance(field, models.DateField):
                if isinstance(field.default, (datetime.datetime, datetime.date)):
                    d['default'] = 0
                elif isinstance(field.default, (datetime.timedelta)):
                    d['default'] = field.get_default().total_seconds()
                else:
                    d['placeholder'] = _('Automatic field')
            else:
                d['default'] = field.get_default()
        if field.help_text:
            d['help'] = field.help_text
        if field.max_length:
            d['max'] = field.max_length

        fields[field.name] = d

    return fields
