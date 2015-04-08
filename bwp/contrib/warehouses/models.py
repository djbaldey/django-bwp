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
from django.db.models import Count, Sum
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from bwp.contrib.abstracts.models import *
from bwp.conf import settings

PARTNER_MODEL = User

NOMENCLATURE_MODEL = getattr(settings, 'NOMENCLATURE_MODEL', None)

if not NOMENCLATURE_MODEL:
    class Nomenclature(AbstractGroup):
        """
        Номенклатура
        """

        class Meta:
            ordering            = ['title']
            verbose_name        = _('nomenclature')
            verbose_name_plural = _('nomenclatures')

    NOMENCLATURE_MODEL = Nomenclature


class AbstractWarehouse(AbstractGroupUnique):
    """
    Внутренний склад или склад поставщика.
    Модель для наследования.
    """

    class Meta:
        abstract = True

class Warehouse(AbstractWarehouse):
    """ Склад """
    #~ service_printer  = models.ForeignKey(RemoteDevice, verbose_name=_('service printer'),
        #~ null=True, blank=True)

    class Meta:
        ordering            = ['title']
        verbose_name        = _('warehouse')
        verbose_name_plural = _('warehouses')

class AbstractDocument(AbstractDocumentDateTime):
    """
    Документ движения по складу.
    Модель для наследования.
    """
    class Meta:
        ordering            = ['-date_time', '-id']
        verbose_name        = _('document')
        verbose_name_plural = _('documents')
        abstract            = True

    def save(self, **kwargs):
        change_dt = False
        if self.pk:
            old = self.__class__.objects.get(pk=self.pk)
            if old.date_time != self.date_time:
                change_dt = True
        else:
            change_dt = True

        super(AbstractDocument, self).save(**kwargs)

        if change_dt:
            stocks = Stock.objects.filter(document_id=self.pk)
            stocks = stocks.exclude(kind=Stock.MOVING_IN)
            #~ print stocks
            stocks.update(date_time=self.date_time)

class DocumentManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(DocumentManager, self).get_query_set(
        ).annotate(summa=Sum('parties__doc_summa'))

class Document(AbstractDocument):
    """
    Документ движения по складу
    """
    INCOMING  = 1
    OUTCOMING = 2
    MOVING    = 3
    INVENTORY = 4
    KIND_CHOICES = (
        (INCOMING,  _('incoming')),
        (OUTCOMING, _('outcoming')),
        (MOVING,    _('moving')),
        (INVENTORY, _('inventory')),
    )
    kind = models.IntegerField(_('kind'), choices=KIND_CHOICES)

    warehouse          = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        related_name='document_set')
    warehouse_other    = models.ForeignKey(Warehouse, verbose_name=_('other warehouse'),
        null=True, blank=True, related_name='document_other_set')
    partner            = models.ForeignKey(PARTNER_MODEL, verbose_name=_('partner'),
        null=True, blank=True, related_name='warehouses_document_set')
    base_document      = models.CharField(_('base document'),
        max_length=255, null=True, blank=True)
    base_document_date = models.DateField(_("base document date"),
        null=True, blank=True)
    base_document_info  = models.TextField(_('base document info'),
        null=True, blank=True)

    default_manager = models.Manager()
    objects = DocumentManager()

    def __unicode__(self):
        if self.pk:
            doc = self.get_kind_display()
            doc = doc.title()
            return _('%(document)s from %(date)s') % {
                'document': doc,
                'date': dateformat.format(timezone.localtime(self.date_time),
                    'Y-m-d H:i:s') if self.date_time else 'None'
            }
        else:
            return _('New document')

    class Meta:
        ordering            = ['-date_time', '-id']
        verbose_name        = _('document')
        verbose_name_plural = _('documents')

DOCUMENT_DB_TABLE = Document()._meta.db_table

class MovingManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(MovingManager, self).get_query_set().filter(
            kind=Document.MOVING).annotate(summa=Sum('parties__doc_summa'))

class Moving(AbstractDocument):
    """ Перемещение """
    kind = models.IntegerField(_('kind'), default=Document.MOVING, editable=False)
    warehouse_other = models.ForeignKey(Warehouse, verbose_name=_('from warehouse'),
        related_name='moving_other_set')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        related_name='moving_set')

    default_manager = models.Manager()
    objects = MovingManager()

    class Meta:
        ordering            = ['-date_time', '-id']
        verbose_name        = _('moving')
        verbose_name_plural = _('movings')
        managed             = False
        db_table            = DOCUMENT_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Document.MOVING
        super(Moving, self).save(**kwargs)

class IncomingManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(IncomingManager, self).get_query_set().filter(
            kind=Document.INCOMING).annotate(summa=Sum('parties__doc_summa'))

class Incoming(AbstractDocument):
    """ Приход """
    kind = models.IntegerField(_('kind'), default=Document.INCOMING, editable=False)
    warehouse           = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        related_name='incoming_set')
    warehouse_other     = models.ForeignKey(Warehouse, verbose_name=_('from warehouse'),
        null=True, blank=True, related_name='incoming_other_set')
    partner             = models.ForeignKey(PARTNER_MODEL, verbose_name=_('partner'),
        null=True, blank=True, related_name='warehouses_incoming_set')
    base_document       = models.CharField(_('base document'),
        max_length=255, null=True, blank=True)
    base_document_date  = models.DateField(_("base document date"),
        null=True, blank=True)
    base_document_info  = models.TextField(_('base document info'),
        null=True, blank=True)

    default_manager = models.Manager()
    objects = IncomingManager()

    class Meta:
        ordering            = ['-date_time', '-id']
        verbose_name        = _('incoming')
        verbose_name_plural = _('incomings')
        managed             = False
        db_table            = DOCUMENT_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Document.INCOMING
        super(Incoming, self).save(**kwargs)

class OutcomingManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(OutcomingManager, self).get_query_set().filter(
            kind=Document.OUTCOMING).annotate(summa=Sum('parties__doc_summa'))

class Outcoming(AbstractDocument):
    """ Списание """
    kind = models.IntegerField(_('kind'), default=Document.OUTCOMING, editable=False)
    warehouse           = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        related_name='outcoming_set')
    warehouse_other     = models.ForeignKey(Warehouse, verbose_name=_('to warehouse'),
        null=True, blank=True, editable=False, related_name='outcoming_other_set')
    partner             = models.ForeignKey(PARTNER_MODEL, verbose_name=_('partner'),
        null=True, blank=True, related_name='warehouses_outcoming_set')
    base_document       = models.CharField(_('base document'),
        max_length=255, null=True, blank=True)
    base_document_date  = models.DateField(_("base document date"),
        null=True, blank=True)
    base_document_info  = models.TextField(_('base document info'),
        null=True, blank=True)

    default_manager = models.Manager()
    objects = OutcomingManager()

    class Meta:
        ordering = ['-date_time', '-id']
        verbose_name = _('outcoming')
        verbose_name_plural = _('outcomings')
        managed = False
        db_table = DOCUMENT_DB_TABLE

    def save(self, **kwargs):
        self.kind = Document.OUTCOMING
        super(Outcoming, self).save(**kwargs)

class InventoryManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(InventoryManager, self).get_query_set().filter(
            kind=Document.INVENTORY).annotate(summa=Sum('parties__diff_summa'))

class Inventory(AbstractDocument):
    """ Инвентаризация """
    kind      = models.IntegerField(_('kind'), default=Document.INVENTORY, editable=False)
    warehouse = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        related_name='inventory_set')

    default_manager = models.Manager()
    objects = InventoryManager()

    class Meta:
        ordering = ['-date_time', '-id']
        verbose_name = _('inventory')
        verbose_name_plural = _('inventories')
        managed = False
        db_table = DOCUMENT_DB_TABLE

    def save(self, **kwargs):
        self.kind = Document.INVENTORY
        super(Inventory, self).save(**kwargs)


class BasePartitioningManager(models.Manager):
    """
    Обычный менеджер, но не устанавливает self.pk в методе `save`,
    это требуется, когда таблицы партиционируются в СУБД и база данных
    не возвращает вставленную строку обратно на клиента.
    """
    def _insert(self, objs, fields, return_id=False, **kwargs):
        return super(BasePartitioningManager, self)._insert(objs, fields, return_id=False, **kwargs)

class AbstractStock(models.Model):
    """
    Движения по складам.
    """
    created   = models.DateTimeField(auto_now_add=True)
    updated   = models.DateTimeField(auto_now=True)
    date_time = models.DateTimeField(_("date and time"), null=True, editable=False)

    _base_manager = BasePartitioningManager()

    def __unicode__(self):
        if hasattr(self, 'document'):
            return unicode(self.document)
        return u'%s %s' % (unicode(_('stock moving')), self.pk)

    class Meta:
        abstract = True

    def warehouse_bwp(self):
        w = self.warehouse
        return {
            'model': str(w._meta),
            'pk': w.pk,
            'label': unicode(w),
        }

    def document_bwp(self):
        d = self.document
        return {
            'model': str(d._meta),
            'pk': d.pk,
            'label': unicode(d),
        }

    def save(self, **kwargs):
        self.date_time = self.document.date_time
        super(AbstractStock, self).save(**kwargs)

class Stock(AbstractStock):
    """
    Движения по складам.
    """
    INCOMING   = '+'
    OUTCOMING  = '-'
    MOVING_OUT = '<'
    MOVING_IN  = '>'
    INVENTORY  = '='
    KIND_CHOICES = (
        (INCOMING,   _('incoming')),
        (OUTCOMING,  _('outcoming')),
        (MOVING_OUT, _('moving out')),
        (MOVING_IN,  _('moving in')),
        (INVENTORY,  _('inventory')),
    )
    kind = models.CharField(_('kind'), max_length=1, choices=KIND_CHOICES, db_index=True)

    document        = models.ForeignKey(Document, verbose_name=_('document'),
        related_name='parties')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        related_name='warehouse')
    nomenclature    = models.ForeignKey(NOMENCLATURE_MODEL, verbose_name=_('nomenclature'),
        related_name='warehouses_stock_set')
    doc_count       = models.FloatField(_('document count'),    null=True, blank=True, default=0)
    doc_price       = models.FloatField(_('document price'),    null=True, blank=True, default=0)
    doc_summa       = models.FloatField(_('document summa'),    null=True, editable=False)
    count           = models.FloatField(_('count'),             null=True, editable=False)
    price           = models.FloatField(_('price'),             null=True, editable=False)
    summa           = models.FloatField(_('summa'),             null=True, editable=False)
    diff            = models.FloatField(_('diff'),              null=True, editable=False)
    diff_summa      = models.FloatField(_('diff summa'),        null=True, editable=False)
    parent          = models.OneToOneField('Stock', verbose_name=_('parent'),
        null=True, related_name='child', editable=False)

    _trigger_lock = models.NullBooleanField(_('lock update'), null=True, default=False, editable=False)

    objects = models.Manager()

    def __unicode__(self):
        return unicode(self.nomenclature)

    class Meta:
        ordering = ['-date_time', '-id', 'nomenclature', 'document__warehouse']
        verbose_name = _('stock')
        verbose_name_plural = _('stocks')
        get_latest_by = 'document__date_time'
        unique_together = ('kind', 'nomenclature', 'document') # Возможно это лишнее в партионном учёте

    def save(self, **kwargs):
        if self.pk:
            old = Stock.objects.get(pk=self.pk)
            self.kind = old.kind
            self.document = old.document
            self.warehouse = old.warehouse
            self.nomenclature = old.nomenclature
        if self.kind == Stock.MOVING_IN:
            raise RuntimeError(
                ('This entry should be edited automatically. ',
                'To do this, edit moving from a warehouse.')
            )

        super(Stock, self).save(**kwargs)

    def delete(self, **kwargs):
        if self.kind == Stock.MOVING_IN:
            raise RuntimeError(
                ('This entry should be removed automatically. ',
                'To do this, remove moving from a warehouse.')
            )
        super(Stock, self).delete(**kwargs)


STOCK_DB_TABLE = Stock()._meta.db_table

class StockMovingOutManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(StockMovingOutManager, self).get_query_set().filter(
            kind=Stock.MOVING_OUT)

class StockMovingOut(AbstractStock):
    """ Партия перемещения со склада """
    kind = models.CharField(_('kind'), editable=False,
        max_length=1, default=Stock.MOVING_OUT)
    document        = models.ForeignKey(Moving, verbose_name=_('document'),
        related_name='out_parties')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        editable=False)
    nomenclature    = models.ForeignKey(NOMENCLATURE_MODEL, verbose_name=_('nomenclature'),
        related_name='warehouses_stockmovingout_set')
    doc_count       = models.FloatField(_('count'))
    doc_price       = models.FloatField(_('price'), editable=False)
    doc_summa       = models.FloatField(_('summa'), editable=False)
    #~ count           = models.FloatField(_('stock count'), editable=False)
    #~ price           = models.FloatField(_('stock price'), editable=False)
    #~ summa           = models.FloatField(_('stock summa'), editable=False)
    #~ diff            = models.FloatField(_('diff'),  editable=False)

    objects = StockMovingOutManager()

    class Meta:
        ordering            = ['-document__date_time', '-document__id', '-id']
        verbose_name        = _('party')
        verbose_name_plural = _("party's move from warehouse")
        managed             = False
        db_table            = STOCK_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Stock.MOVING_OUT
        self.warehouse = self.document.warehouse_other
        super(StockMovingOut, self).save(**kwargs)

class StockMovingInManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(StockMovingInManager, self).get_query_set().filter(
            kind=Stock.MOVING_IN)

class StockMovingIn(AbstractStock):
    """ Партия перемещения на склад """
    kind = models.CharField(_('kind'), editable=False,
        max_length=1, default=Stock.MOVING_IN)
    document        = models.ForeignKey(Moving, verbose_name=_('document'),
        related_name='parties')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        editable=False)
    nomenclature    = models.ForeignKey(NOMENCLATURE_MODEL, verbose_name=_('nomenclature'),
        related_name='warehouses_stockmovingin_set')
    doc_count       = models.FloatField(_('count'))
    doc_price       = models.FloatField(_('price'), editable=False)
    doc_summa       = models.FloatField(_('summa'), editable=False)
    #~ count           = models.FloatField(_('stock count'), editable=False)
    #~ price           = models.FloatField(_('stock price'), editable=False)
    #~ summa           = models.FloatField(_('stock summa'), editable=False)
    #~ diff            = models.FloatField(_('diff'),  editable=False)

    objects = StockMovingInManager()

    class Meta:
        ordering            = ['-document__date_time', '-document__id', '-id']
        verbose_name        = _('party')
        verbose_name_plural = _("party's move to warehouse")
        managed             = False
        db_table            = STOCK_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Stock.MOVING_IN
        self.warehouse = self.document.warehouse
        super(StockMovingIn, self).save(**kwargs)

class StockIncomingManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(StockIncomingManager, self).get_query_set().filter(
            kind=Stock.INCOMING)

class StockIncoming(AbstractStock):
    """ Партия прихода на склад """
    kind            = models.CharField(_('kind'), editable=False,
        max_length=1, default=Stock.INCOMING)
    document        = models.ForeignKey(Incoming, verbose_name=_('document'),
        related_name='parties')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        editable=False)
    nomenclature    = models.ForeignKey(NOMENCLATURE_MODEL, verbose_name=_('nomenclature'),
        related_name='warehouses_stockincoming_set')
    doc_count       = models.FloatField(_('count'))
    doc_summa       = models.FloatField(_('summa'))
    doc_price       = models.FloatField(_('price'), editable=False)
    #~ count           = models.FloatField(_('stock count'), editable=False)
    #~ price           = models.FloatField(_('stock price'), editable=False)
    #~ summa           = models.FloatField(_('stock summa'), editable=False)
    #~ diff            = models.FloatField(_('diff'),  editable=False)

    objects = StockIncomingManager()

    class Meta:
        ordering            = ['-document__date_time', '-document__id', '-id']
        verbose_name        = _('party')
        verbose_name_plural = _("party's incoming")
        managed             = False
        db_table            = STOCK_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Stock.INCOMING
        self.warehouse = self.document.warehouse
        # Подсчёт цены выполняется в триггерной процедуре базы данных:
        # self.doc_price = 1.0 * self.doc_summa / self.doc_count
        super(StockIncoming, self).save(**kwargs)

class StockOutcomingManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(StockOutcomingManager, self).get_query_set().filter(
            kind=Stock.OUTCOMING)

class StockOutcoming(AbstractStock):
    """ Партия расхода со склада """
    kind            = models.CharField(_('kind'), editable=False,
        max_length=1, default=Stock.OUTCOMING)
    document        = models.ForeignKey(Outcoming, verbose_name=_('document'),
        related_name='parties')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        editable=False)
    nomenclature    = models.ForeignKey(NOMENCLATURE_MODEL, verbose_name=_('nomenclature'),
        related_name='warehouses_stockoutcoming_set')
    doc_count       = models.FloatField(_('count'))
    doc_price       = models.FloatField(_('price'), editable=False)
    doc_summa       = models.FloatField(_('summa'), editable=False)
    #~ count           = models.FloatField(_('stock count'), editable=False)
    #~ price           = models.FloatField(_('stock price'), editable=False)
    #~ summa           = models.FloatField(_('stock summa'), editable=False)
    #~ diff            = models.FloatField(_('diff'),  editable=False)

    objects = StockOutcomingManager()

    class Meta:
        ordering            = ['-document__date_time', '-document__id', '-id']
        verbose_name        = _('party')
        verbose_name_plural = _("party's outcoming")
        managed             = False
        db_table            = STOCK_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Stock.OUTCOMING
        self.warehouse = self.document.warehouse
        super(StockOutcoming, self).save(**kwargs)

class StockInventoryManager(models.Manager):
    use_for_related_fields = True
    def get_query_set(self):
        return super(StockInventoryManager, self).get_query_set().filter(
            kind=Stock.INVENTORY)

class StockInventory(AbstractStock):
    """ Партия ревизии на складе """
    kind            = models.CharField(_('kind'), editable=False,
        max_length=1, default=Stock.INVENTORY)
    document        = models.ForeignKey(Inventory, verbose_name=_('document'),
        related_name='parties')
    warehouse       = models.ForeignKey(Warehouse, verbose_name=_('warehouse'),
        editable=False)
    nomenclature    = models.ForeignKey(NOMENCLATURE_MODEL, verbose_name=_('nomenclature'),
        related_name='warehouses_stockinventory_set')
    doc_count       = models.FloatField(_('count'))
    doc_price       = models.FloatField(_('price'), editable=False)
    doc_summa       = models.FloatField(_('summa'), editable=False)
    #~ count           = models.FloatField(_('stock count'), editable=False)
    #~ price           = models.FloatField(_('stock price'), editable=False)
    #~ summa           = models.FloatField(_('stock summa'), editable=False)
    diff            = models.FloatField(_('diff'),  editable=False)
    diff_summa      = models.FloatField(_('diff summa'), null=True, editable=False)

    objects = StockInventoryManager()

    class Meta:
        ordering            = ['-document__date_time', '-document__id', '-id']
        verbose_name        = _('party')
        verbose_name_plural = _("party's inventory")
        managed             = False
        db_table            = STOCK_DB_TABLE
    
    def save(self, **kwargs):
        self.kind = Stock.INVENTORY
        self.warehouse = self.document.warehouse
        super(StockInventory, self).save(**kwargs)

