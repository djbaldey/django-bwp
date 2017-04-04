# -*- coding: utf-8 -*-
#
#  bwp/utils/filters.py
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
from django.db.models import Q, Model
import operator


def filterQueryset(queryset, search_fields, query):
    """ Фильтрация """
    if search_fields:
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name
        orm_lookups = [
            construct_search(str(search_field)) for search_field in
            search_fields
        ]
        if query not in ('', None, False, True):
            for bit in query.split():
                or_queries = [
                    Q(**{orm_lookup: bit}) for orm_lookup in
                    orm_lookups
                ]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
    return queryset


def get_object_or_none(qs, **kwargs):
    """ Возвращает объект или None.
        На вход можно подавать как класс модели, так и отфильтрованный
        QuerySet.
    """
    if type(qs) == type(Model):
        try:
            return qs.objects.get(**kwargs)
        except Exception:
            return None
    try:
        return qs.get(**kwargs)
    except Exception:
        return None
