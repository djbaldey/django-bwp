# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2013 Grigoriy Kramarenko.
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
from django.utils import simplejson
from copy import deepcopy
from django.core.serializers.json import DjangoJSONEncoder

class GeneralWidget(object):
    field = None
    is_configured = False
    is_hidden = False
    tag = None
    attr = None

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self.__dict__[key] = val
        if self.attr is None:
            self.attr = {}

    def __str__(self):
        dic = self.get_dict()
        #~ del dic['field']
        return simplejson.dumps(dic, ensure_ascii=False,
                                cls=DjangoJSONEncoder,
                                indent=4,
                            ).encode('utf-8', 'ignore')

    def __unicode__(self):
        return self.__str__()

    def get_dict(self):
        d = {
            'name': self.field.name,
            'label': unicode(self.field.verbose_name),
            'hidden': self.is_hidden,
            'tag': self.tag,
            'attr': self.attr,
        }
        if self.is_hidden and not self.attr.has_key('hidden'):
            d['attr']['hidden'] = self.is_hidden
        if hasattr(self, 'select_multiple') and not self.attr.has_key('multiple'):
            d['attr']['multiple'] = self.select_multiple
        if hasattr(self, 'input_type') and not self.attr.has_key('type'):
            d['attr']['type'] = self.input_type
        return d

class SelectWidget(GeneralWidget):
    tag = 'select'

class SelectMultipleWidget(SelectWidget):
    select_multiple = True

class InputWidget(GeneralWidget):
    tag = 'input'
    input_type = 'text'

class HiddenWidget(InputWidget):
    is_hidden = True

class PasswordWidget(InputWidget):
    tag = 'input'
    input_type = 'text'

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

WIDGETS_FOR_DBFIELD = {
    models.ForeignKey:                  (SelectWidget, None),
    models.ManyToManyField:             (SelectMultipleWidget, None),
    models.OneToOneField:               (SelectWidget, None),
    models.AutoField:                   (HiddenWidget, {'class': 'integerfield'}),
    models.BigIntegerField:             (InputWidget, {'class': 'bigintegerfield'}),
    models.BooleanField:                (CheckboxWidget, None),
    models.CharField:                   (InputWidget, None),
    models.CommaSeparatedIntegerField:  (InputWidget, None),
    models.DateField:                   (InputWidget, {'class': 'datefield'}),
    models.DateTimeField:               (InputWidget, {'class': 'datetimefield'}),
    models.DecimalField:                (InputWidget, {'class': 'decimalfield'}),
    models.EmailField:                  (EmailWidget, None),
    models.FileField:                   (FileWidget, None),
    models.FilePathField:               (InputWidget, {'class': 'filepathfield'}),
    models.FloatField:                  (InputWidget, {'class': 'floatfield'}),
    models.ImageField:                  (ImageWidget, None),
    models.IntegerField:                (InputWidget, {'class': 'integerfield'}),
    models.IPAddressField:              (InputWidget, {'class': 'ipaddressfield'}),
    models.GenericIPAddressField:       (InputWidget, {'class': 'ipaddressfield'}),
    models.NullBooleanField:            (InputWidget, {'class': 'nullbooleanfield'}),
    models.PositiveIntegerField:        (InputWidget, {'class': 'positiveintegerfield'}),
    models.PositiveSmallIntegerField:   (InputWidget, {'class': 'positivesmallintegerfield'}),
    models.SlugField:                   (InputWidget, {'class': 'slugfield'}),
    models.SmallIntegerField:           (InputWidget,{'class': 'smallintegerfield'}),
    models.TextField:                   (InputWidget, None),
    models.TimeField:                   (InputWidget, {'class': 'timefield'}),
    models.URLField:                    (URLWidget, None),
}

def get_widget_from_field(field):
    try:
        widget_class, attr = WIDGETS_FOR_DBFIELD[type(field)]
    except:
        widget_class, attr = (InputWidget, None)
    if attr is None:
        attr = {}
    else:
        attr = deepcopy(attr)
    widget = widget_class(field=field, attr=attr)
    print widget
    return widget
