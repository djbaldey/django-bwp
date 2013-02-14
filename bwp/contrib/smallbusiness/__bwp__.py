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
from bwp.models import ModelBWP
from models import *

class PostAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
site.register(Post, PostAdmin)

class EmployeeAdmin(ModelBWP):
    list_display = ('__unicode__', 'org', 'id')
site.register(Employee, EmployeeAdmin)

class ClientAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
site.register(Client, ClientAdmin)

class UnitAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['qualifier']
site.register(Unit, UnitAdmin)

class GoodGroupAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
site.register(GoodGroup, GoodGroupAdmin)

class GoodAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['group', 'unit', 'package']
site.register(Good, GoodAdmin)

class PriceAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['good']
site.register(Price, PriceAdmin)

class SpecAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['price']
site.register(Spec, SpecAdmin)

class ContractAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['user']
site.register(Contract, ContractAdmin)

class InvoiceAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['user']
site.register(Invoice, InvoiceAdmin)

class PaymentAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['user']
site.register(Payment, PaymentAdmin)

class ActAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
site.register(Act, ActAdmin)

