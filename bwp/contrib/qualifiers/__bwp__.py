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
from bwp import core as admin
from models import *

class CountryAdmin(admin.ModelBWP):
    list_display = ('title', 'code')
    search_fields = ['title', 'code']
    ordering = ['title']
admin.site.register(Country, CountryAdmin)

class CurrencyAdmin(admin.ModelBWP):
    list_display = ('title', 'code',)
    search_fields = ['title', 'countries__title','code']
    filter_horizontal = ['countries']
    ordering = ['title']
admin.site.register(Currency, CurrencyAdmin)

class DocumentAdmin(admin.ModelBWP):
    list_display = ('title', 'code',)
    search_fields = ['title', 'code','parent__code']
    #~ list_filter = ('parent', )
    raw_id_fields = ['parent']
    ordering = ['title']
admin.site.register(Document, DocumentAdmin)

class MeasureUnitCategoryAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(MeasureUnitCategory, MeasureUnitCategoryAdmin)

class MeasureUnitGroupAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(MeasureUnitGroup, MeasureUnitGroupAdmin)

class MeasureUnitAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'code')
    list_filter = ('category', 'group')
    search_fields = ['title', 'code',]
admin.site.register(MeasureUnit, MeasureUnitAdmin)

