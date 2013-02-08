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
from bwp import core as admin
from django.utils.translation import ugettext_lazy as _
from models import *

class PostAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(Post, PostAdmin)

class EmployeeAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(Employee, EmployeeAdmin)

class ClientAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(Client, ClientAdmin)

class UnitAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['qualifier']
admin.site.register(Unit, UnitAdmin)

class GoodGroupAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(GoodGroup, GoodGroupAdmin)

class GoodAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['group', 'unit', 'package']
admin.site.register(Good, GoodAdmin)

class PriceAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['good']
admin.site.register(Price, PriceAdmin)

class SpecAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['price']
admin.site.register(Spec, SpecAdmin)

class ContractAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['user']
admin.site.register(Contract, ContractAdmin)

class InvoiceAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['user']
admin.site.register(Invoice, InvoiceAdmin)

class PaymentAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
    raw_id_fields = ['user']
admin.site.register(Payment, PaymentAdmin)

class ActAdmin(admin.ModelBWP):
    list_display = ('__unicode__', 'id')
admin.site.register(Act, ActAdmin)

