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
from bwp.models import ModelBWP, ComposeBWP
from models import *

site.register(NOMENCLATURE_MODEL, ModelBWP)

site.register(Warehouse, ModelBWP)

class PartyCompose(ComposeBWP):
    verbose_name = _('parties')
    list_display = (
        'nomenclature',
        'doc_count',
        'doc_price',
        'doc_summa',
        'id',
    )

class StockCompose(PartyCompose):
    model = Stock

class StockMovingOutCompose(PartyCompose):
    model = StockMovingOut
    #~ verbose_name = _('from warehouse')

class StockMovingInCompose(PartyCompose):
    model = StockMovingIn
    #~ verbose_name = _('to warehouse')

class StockIncomingCompose(PartyCompose):
    model = StockIncoming

class StockOutcomingCompose(PartyCompose):
    model = StockOutcoming

class StockInventoryCompose(PartyCompose):
    model = StockInventory

class DocumentBWP(ModelBWP):
    manager = Document.objects
    list_display = (
        '__unicode__',
        ('summa', _('summa')),
        'id',
    )
    compositions = [
        ('parties',     StockCompose),
    ]

site.register(Document, DocumentBWP)

class MovingBWP(DocumentBWP):
    manager = Moving.objects
    compositions = [
        ('out_parties', StockMovingOutCompose),
        #~ ('parties', StockMovingInCompose),
    ]
site.register(Moving, MovingBWP)

class IncomingBWP(DocumentBWP):
    manager = Incoming.objects
    compositions = [
        ('parties', StockIncomingCompose),
    ]
site.register(Incoming, IncomingBWP)

class OutcomingBWP(DocumentBWP):
    manager = Outcoming.objects
    compositions = [
        ('parties', StockOutcomingCompose),
    ]
site.register(Outcoming, OutcomingBWP)

class InventoryBWP(DocumentBWP):
    manager = Inventory.objects
    compositions = [
        ('parties', StockInventoryCompose),
    ]
site.register(Inventory, InventoryBWP)

class StockBWP(ModelBWP):
    list_display = (
        '__unicode__',
        'doc_count',
        'doc_price',
        'doc_summa',
        'count',
        'price',
        'summa',
        'kind',
        'diff',
        ('warehouse_bwp', _('warehouse')),
        ('document_bwp', _('document')),
        'id',
    )

site.register(Stock, StockBWP)
site.register(StockMovingOut, ModelBWP)
site.register(StockMovingIn, ModelBWP)
site.register(StockIncoming, ModelBWP)
site.register(StockOutcoming, ModelBWP)
site.register(StockInventory, ModelBWP)
