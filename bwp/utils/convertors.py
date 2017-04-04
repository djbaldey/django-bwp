# -*- coding: utf-8 -*-
#
#  bwp/utils/convertors.py
#
#  Copyright 2012 Grigoriy Kramarenko <root@rosix.ru>
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
from django.db.models.query import QuerySet
from django.core.paginator import Page

from bwp import serializers


def serialize(objects, **options):
    """ Сериализатор в объект(ы) Python, принимает либо один,
        либо несколько django-объектов или объект паджинации
        и точно также возвращает.
    """
    if ('use_split_keys' not in options and 'use_natural_keys' not in options):
        # default
        options['use_split_keys'] = True

    if isinstance(objects, (QuerySet, Page, list, tuple)):
        # Список объектов
        data = serializers.serialize('python', objects, **options)
    else:
        # Единственный объект
        data = serializers.serialize('python', [objects], **options)[0]
    return data


def jquery_form_array(array):
    """ Преобразование объекта параметров, полученных jQuery:
        array = form.serializeArray())
        например:
        [{name:'a', value:1}, {name:'a', value:2}, {name:'b', value:3}]
        вернёт:
        {'a': [1,2], 'b': 3}
    """
    d = {}

    def append(key, value):
        if key in d.keys():
            if isinstance(d[key], list):
                d[key].append(value)
            else:
                d[key] = [d[key]]
                d[key].append(value)
        else:
            d[key] = value
    for i in array:
        append(i['name'], i['value'])
    return d


def jquery_multi_form_array(array):
    """ Преобразование объекта множества параметров, полученных jQuery:
        array = []
        array.push(form1.serializeArray())
        array.push(form2.serializeArray())
    """
    return [jquery_form_array(a) for a in array]
