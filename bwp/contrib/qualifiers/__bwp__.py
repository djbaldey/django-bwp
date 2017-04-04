# -*- coding: utf-8 -*-
#
#  bwp/contrib/qualifiers/__bwp__.py
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
from bwp.sites import site
from bwp.models import ModelBWP, ComposeBWP
from models import Country, Currency, Document, MeasureUnit, \
    MeasureUnitCategory, MeasureUnitGroup


class CountryAdmin(ModelBWP):
    list_display = ('title', 'code')
    list_display_css = {'code': 'input-micro'}
    search_fields = ['title', 'code']
    ordering = ['title']


site.register(Country, CountryAdmin)


class CurrencyAdmin(ModelBWP):
    list_display = ('title', 'code')
    list_display_css = {'code': 'input-micro'}
    search_fields = ['title', 'countries__title', 'code']
    filter_horizontal = ['countries']
    ordering = ['title', 'code']


site.register(Currency, CurrencyAdmin)


class DocumentCompose(ComposeBWP):
    model = Document


class DocumentAdmin(ModelBWP):
    list_display = ('title', 'code')
    list_display_css = {'code': 'input-micro'}
    search_fields = ['title', 'code', 'parent__code']
    raw_id_fields = ['parent']
    ordering = ['title']
    compositions = [('document_set', DocumentCompose)]


site.register(Document, DocumentAdmin)


class MeasureUnitCompose(ComposeBWP):
    model = MeasureUnit


class MeasureUnitCategoryAdmin(ModelBWP):
    list_display = ('title', 'id')
    compositions = [('measureunit_set', MeasureUnitCompose)]


site.register(MeasureUnitCategory, MeasureUnitCategoryAdmin)


class MeasureUnitGroupAdmin(ModelBWP):
    list_display = ('title', 'id')
    compositions = [('measureunit_set', MeasureUnitCompose)]


site.register(MeasureUnitGroup, MeasureUnitGroupAdmin)


class MeasureUnitAdmin(ModelBWP):
    list_display = ('title', 'note_ru', 'note_iso', 'symbol_ru',
                    'symbol_iso', 'category', 'group', 'code')
    list_display_css = {
        'code': 'input-micro',
        'note_ru': 'input-mini',
        'symbol_ru': 'input-mini',
        'note_iso': 'input-mini',
        'symbol_iso': 'input-mini',
    }
    list_filter = ('category', 'group')
    search_fields = ['title', 'code', 'category__title', 'group__title']


site.register(MeasureUnit, MeasureUnitAdmin)
