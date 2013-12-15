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
from django.utils.translation import ugettext_lazy as _
from bwp.sites import site
from bwp.models import ModelBWP, ComponentBWP
from models import *

class CountryBWP(ModelBWP):
    columns = ('title', 'code')
    fields_search = ['title', 'code']
    ordering = ['title']
site.register(Country, CountryBWP)

class CurrencyBWP(ModelBWP):
    columns = ('title', 'code',)
    fields_search = ['title', 'countries__title','code']
    ordering = ['title', 'code']
site.register(Currency, CurrencyBWP)

class DocumentComponent(ComponentBWP):
    site = site
    model = Document

class DocumentBWP(ModelBWP):
    columns = ('title', 'code',)
    fields_search = ['title', 'code','parent__code']
    ordering = ['title']
    components = [DocumentComponent(field='parent')]
site.register(Document, DocumentBWP)

class MeasureUnitComponent(ComponentBWP):
    site = site
    model = MeasureUnit

class MeasureUnitCategoryBWP(ModelBWP):
    columns = ('title', 'id')
    components = [MeasureUnitComponent(field='group')]
site.register(MeasureUnitCategory, MeasureUnitCategoryBWP)

class MeasureUnitGroupBWP(ModelBWP):
    columns = ('title', 'id')
    components = [MeasureUnitComponent(field='category')]
site.register(MeasureUnitGroup, MeasureUnitGroupBWP)


class MeasureUnitBWP(ModelBWP):
    columns = ('title', 'note_ru', 'note_iso', 'symbol_ru',
                    'symbol_iso', 'category','group', 'code')

    #~ list_filter = ('category', 'group')
    fields_search = ['title', 'code', 'category__title', 'group__title']
site.register(MeasureUnit, MeasureUnitBWP)

