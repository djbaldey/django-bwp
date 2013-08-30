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
from StringIO import StringIO
from types import MethodType 
from django.conf import settings
from django.core.serializers import base
from django.db import models, DEFAULT_DB_ALIAS
from django.utils.encoding import smart_unicode, is_protected_type
from django.core.paginator import Page
from bwp.utils.pagers import page_range_dots
from datetime import datetime, date, time

from django.core.serializers.python import Serializer as OrignSerializer

class SerializerWrapper(object):
    """ Обёртка вокруг базовых классов Django.
        Переопределяет их методы.
    """
    def handle_field(self, obj, field):
        value = field._get_val_from_obj(obj)
        # Protected types (i.e., primitives like None, numbers, dates,
        # and Decimals) are passed through as is. All other values are
        # converted to string first.
        if is_protected_type(value):
            if   isinstance(value, datetime):
                val = value.isoformat()
                val = val.split('.')[0] # обрезаем милисекунды
                val = val.replace(' ', 'T') # на случай, если не локальное время 
            elif isinstance(value, (date, time)):
                val = value.isoformat()
            else:
                val = value
            self._current[field.name] = val
        elif field.name == 'password':
            self._current[field.name] = ''
        else:
            self._current[field.name] = field.value_to_string(obj)
        return self._current[field.name]

    def handle_properties(self, obj, name):
        value = getattr(obj, name)
        if callable(value):
            value = value()
        # Protected types (i.e., primitives like None, numbers, dates,
        # and Decimals) are passed through as is. All other values are
        # converted to string first.
        if is_protected_type(value):
            if   isinstance(value, datetime):
                val = str(value).split('.')[0] # обрезаем милисекунды
            elif isinstance(value, (date, time)):
                val = str(value)
            else:
                val = value
            self._properties[name] = val
        elif isinstance(value, dict):
            self._properties[name] = value
        else:
            self._properties[name] = unicode(value)
        return self._properties[name]
    
    def handle_fk_field(self, obj, field):
        if obj.pk and (self.use_split_keys or self.use_natural_keys):
            related = getattr(obj, field.name)
            if related:
                if self.use_natural_keys and hasattr(field.rel.to, 'natural_key'):
                    value = related.natural_key()[0]
                elif self.use_split_keys:
                    value = (related.pk, unicode(related))
                else:
                    value = unicode(related)
            else:
                value = None
        else:
            value = getattr(obj, field.get_attname())
            rel_model = field.rel.to
            if self.use_split_keys:
                try:
                    related = rel_model._default_manager.get(pk=value)
                    value = (related.pk, unicode(related))
                except:
                    pass
            
        self._current[field.name] = value

    def handle_m2m_field(self, obj, field):
        if not obj.pk:
            self._current[field.name] = []
        elif field.rel.through._meta.auto_created:
            if self.use_split_keys:
                m2m_value = lambda value: (value.pk, unicode(value))
            elif self.use_natural_keys and hasattr(field.rel.to, 'natural_key'):
                m2m_value = lambda value: value.natural_key()
            else:
                m2m_value = lambda value: smart_unicode(value._get_pk_val(), strings_only=True)
            self._current[field.name] = [m2m_value(related)
                               for related in getattr(obj, field.name).iterator()]

    def serialize_queryset(self, queryset, **options):
        """
        Практически в точности копирует оригинальный метод serialize,
        но не запускает в конце метод окончания сериализации
        """
        self.options = options

        self.stream = options.pop("stream", StringIO())
        self.selected_fields = options.pop("fields", None)
        self.properties = options.pop("properties", [])
        self.use_split_keys = options.pop("use_split_keys", False)
        self.use_natural_keys = options.pop("use_natural_keys", False)
        if self.use_split_keys:
            self.use_natural_keys = False

        self.start_serialization()
        for obj in queryset:
            self.start_object(obj)
            # Use the concrete parent class' _meta instead of the object's _meta
            # This is to avoid local_fields problems for proxy models. Refs #17717.
            concrete_model = obj._meta.concrete_model
            for field in concrete_model._meta.local_fields:
                #~ if field.serialize: # Чтобы сериализовать поля PK нужно отключить это
                    if field.rel is None:
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in concrete_model._meta.many_to_many:
                if field.serialize:
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            for field in self.properties:
                self.handle_properties(obj, field)
            self.end_object(obj)
        return self.objects

    def serialize(self, queryset, **options):
        """
        Serialize a QuerySet or page of Paginator.
        """
        if isinstance(queryset, Page):
            result = {}
            wanted = ("end_index", "has_next", "has_other_pages", "has_previous",
                    "next_page_number", "number", "start_index", "previous_page_number")
            for attr in wanted:
                v = getattr(queryset, attr)
                if isinstance(v, MethodType):
                    try:
                        result[attr] = v()
                    except:
                        result[attr] = None
                elif isinstance(v, (str, int)):
                    result[attr] = v
            result['count'] = queryset.paginator.count
            result['num_pages'] = queryset.paginator.num_pages
            result['per_page']  = queryset.paginator.per_page
            result['page_range'] = page_range_dots(queryset)
            result['object_list'] = self.serialize_queryset(queryset.object_list, **options)
            self.objects = result
        else:
            self.serialize_queryset(queryset, **options)
        self.end_serialization() # Окончательно сериализуем
        return self.getvalue()

    def start_object(self, obj):
        self._current    = {}
        self._properties = {}

    def end_object(self, obj):
        _unicode = ""
        try:
            _unicode = smart_unicode(obj)
        except:
            pass
        self.objects.append({
            "model"  :      smart_unicode(obj._meta),
            "pk"     :      smart_unicode(obj._get_pk_val(), strings_only=True),
            "fields":       self._current,
            "properties":   self._properties,
            "__unicode__" : _unicode,
        })
        self._current    = None
        self._properties = None

class Serializer(SerializerWrapper, OrignSerializer):
    """
    Serializes a QuerySet or page of Paginator to basic Python objects.
    """
    pass

def Deserializer(object_list, **options):
    """
    Deserialize simple Python objects back into Django ORM instances.

    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    db = options.pop('using', DEFAULT_DB_ALIAS)
    use_split_keys = options.pop("use_split_keys", False)
    use_natural_keys = options.pop("use_natural_keys", False)
    models.get_apps()
    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        Model = _get_model(d["model"])
        data = {Model._meta.pk.attname : Model._meta.pk.to_python(d.get("pk", None))}
        m2m_data = {}

        # Handle each field
        for (field_name, field_value) in d["fields"].iteritems():
            if field_name == Model._meta.pk.attname:
                continue
            if isinstance(field_value, str):
                field_value = smart_unicode(field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True)

            field = Model._meta.get_field(field_name)
            if field_value is None:
                field_value = field.get_default()

            # Handle M2M relations
            if field.rel and isinstance(field.rel, models.ManyToManyRel):
                if hasattr(field.rel.to._default_manager, 'get_by_natural_key'):
                    def m2m_convert(value):
                        if hasattr(value, '__iter__'):
                            return field.rel.to._default_manager.db_manager(db).get_by_natural_key(*value).pk
                        else:
                            return smart_unicode(field.rel.to._meta.pk.to_python(value))
                else:
                    m2m_convert = lambda v: smart_unicode(field.rel.to._meta.pk.to_python(v))
                m2m_data[field.name] = [m2m_convert(pk) for pk in field_value]

            # Handle FK fields
            elif field.rel and isinstance(field.rel, models.ManyToOneRel):
                if field_value is not None:
                    if hasattr(field.rel.to._default_manager, 'get_by_natural_key'):
                        if hasattr(field_value, '__iter__'):
                            obj = field.rel.to._default_manager.db_manager(db).get_by_natural_key(*field_value)
                            value = getattr(obj, field.rel.field_name)
                            # If this is a natural foreign key to an object that
                            # has a FK/O2O as the foreign key, use the FK value
                            if field.rel.to._meta.pk.rel:
                                value = value.pk
                        else:
                            value = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                        data[field.attname] = value
                    elif isinstance(field_value, (list,tuple)):
                        data[field.attname] = field_value[0]
                    else:
                        data[field.attname] = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                else:
                    data[field.attname] = None

            # Handle all other fields
            else:
                data[field.name] = field.to_python(field_value)

        yield base.DeserializedObject(Model(**data), m2m_data)

def _get_model(model_identifier):
    """
    Helper to look up a model from an "app_label.module_name" string.
    """
    try:
        Model = models.get_model(*model_identifier.split("."))
    except TypeError:
        Model = None
    if Model is None:
        raise base.DeserializationError(u"Invalid model identifier: '%s'" % model_identifier)
    return Model
