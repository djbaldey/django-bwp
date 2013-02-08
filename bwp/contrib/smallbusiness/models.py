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
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from bwp.contrib.abstracts.models import AbstractGroupUnique, AbstractGroup
from bwp.contrib.contacts.models import Org, Person
from bwp.contrib.qualifiers.models import MeasureUnit, Country, Currency
from bwp.contrib.reports.models import Template
from bwp.db import managers as bwpmanagers, fields
from bwp.utils.classes import upload_to, autonumber

import datetime
import managers

class Post(AbstractGroupUnique):
    """ Должность """

    priority = models.IntegerField(
            default=0,
            verbose_name = _('priority'),
            help_text=_("Priority for ordering"))
    class Meta:
        ordering = ['-priority', 'title',]
        verbose_name = _('post')
        verbose_name_plural = _('posts')

class Employee(models.Model):
    """ Сотрудники """

    person = models.ForeignKey(
            Person,
            verbose_name = _('person'))
    org = models.ForeignKey(
            Org,
            verbose_name = _('organization'))
    post = models.ForeignKey(
            Post,
            verbose_name = _('post'))

    def __unicode__(self):
        return unicode(self.person)

    class Meta:
        ordering = ['org',
                    'person__last_name', 'person__first_name',
                    'person__middle_name']
        verbose_name = _('employee')
        verbose_name_plural = _('employees')
        unique_together = ('person', 'org')

class Client(models.Model):
    """ Клиент, как организация, так и частное лицо """

    org = models.ForeignKey(
            Org,
            null=True, blank=True, unique=True,
            verbose_name = _('org'))
    person = models.ForeignKey(
            Person,
            null=True, blank=True, unique=True,
            verbose_name = _('person'))

    def __unicode__(self):
        return unicode(self.detail)

    class Meta:
        ordering = ['id']
        verbose_name = _('client')
        verbose_name_plural = _('clients')

    @models.permalink
    def get_absolute_url(self):
        detail = self.detail
        if detail:
            return ('%s_detail' % detail.__class__.__name__.lower(), [str(detail.id)])
        else:
            return ('client_create', [str(self.id)])

    @property
    def detail(self):
        if self.person:
            return self.person
        elif self.org:
            return self.org
        return None

    def save(self, **kwargs):
        """ Нельзя сохранить со всеми пустыми полями,
            но если установлены все поля, то сохраняется лишь
            поле организации.
        """
        if not self.detail:
            return False
        if self.person and self.org:
            self.person = None
        super(Client, self).save(**kwargs)

###

class Unit(AbstractGroup):
    """ Единицы измерений """
    qualifier = models.ForeignKey(
            MeasureUnit,
            blank=True, null=True,
            verbose_name = _('qualifier'))

    class Meta:
        ordering = ['qualifier', 'title']
        verbose_name = _('unit')
        verbose_name_plural = _('measure units')

class GoodGroup(AbstractGroup):
    """ Группа товара """
    class Meta:
        ordering = ['title']
        verbose_name = _('group')
        verbose_name_plural = _('good groups')

class Good(AbstractGroup):
    """ Товар """
    country = models.ForeignKey(
            Country,
            blank=True, null=True,
            verbose_name = _('country'))
    gtd = models.CharField(
            max_length=255,
            blank=True,
            verbose_name = _("GTD"))
    unit = models.ForeignKey(
            Unit,
            blank=True, null=True,
            related_name='good_unit_set',
            verbose_name = _('measure'))
    package = models.ForeignKey(
            Unit,
            blank=True, null=True,
            related_name='good_package_set',
            verbose_name = _('package'))
    group = models.ForeignKey(
            GoodGroup,
            blank=True, null=True,
            verbose_name = _('group'))
    about = fields.HTMLField(
            blank=True,
            verbose_name = _("about"))

    class Meta:
        ordering = ['title']
        verbose_name = _('good')
        verbose_name_plural = _('goods')

class Price(models.Model):
    """ Цены на товары """
    NDSTYPE_NOT = 0
    NDSTYPE_ADD = 1
    NDSTYPE_CUT = 2
    NDSTYPE_CHOICES = (
        (NDSTYPE_NOT,_('no')),
        (NDSTYPE_ADD,_('to add')),
        (NDSTYPE_CUT,_('to cut')),
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
            default=True,
            verbose_name = _('is acvive'))
    good = models.ForeignKey(
            Good,
            verbose_name = _('good'))
    price = models.DecimalField(
            max_digits=10, decimal_places=2,
            default=0.0,
            verbose_name = _('price'))
    currency = models.ForeignKey(
            Currency,
            blank=True, null=True,
            verbose_name = _('currency'))
    nds = models.IntegerField(
            blank=True, null=True,
            verbose_name = _('NDS'))
    ndstype = models.IntegerField(
            choices=NDSTYPE_CHOICES,
            default=0,
            verbose_name = _('NDS type'))
    start = models.DateField(
            default=datetime.date.today() + datetime.timedelta(1),
            verbose_name = _('start'))

    objects = models.Manager()
    actives = managers.ActivePriceManager()

    def __unicode__(self):
        return unicode(self.good)

    class Meta:
        ordering = ['good__group__title','good','start',]
        verbose_name = _('price')
        verbose_name_plural = _('prices')
        get_latest_by = 'start'

    def save(self, **kwargs):
        super(Price, self).save(**kwargs)
        
        qs = Price.actives.filter(good=self.good)
        try:
            latest = qs.latest()
            qs = qs.exclude(id=latest.id,)
        except Price.DoesNotExist:
            pass
        qs.update(is_active=False)

    @property
    def NDS(self):
        if not self.nds:
            return 0
        price = float(self.price)
        if self.ndstype == NDSTYPE_ADD:
            # Начислить НДС
            return price * (self.nds/100)
        elif self.ndstype == NDSTYPE_CUT:
            # Выделить НДС
            return price - (price / (1 + self.nds/100))
        else:
            return 0

    @property
    def summa(self):
        if self.nds and self.ndstype == NDSTYPE_ADD:
            # Начислить НДС
            return float(self.price) + self.NDS
        else:
            return float(self.price)

class Spec(models.Model):
    """ Спецификация """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    price = models.ForeignKey(
            Price,
            verbose_name=_('price'))
    count = models.PositiveIntegerField(
            null=True, blank=True,
            verbose_name=_('count'))
    discount = models.PositiveIntegerField(
            default=0,
            verbose_name = _('discount'))

    def __unicode__(self):
        return unicode(self.price)

    class Meta:
        ordering = ['-updated', 'price',]
        verbose_name = _('specification')
        verbose_name_plural = _('specifications')

    @property
    def summa(self):
        s = self.price.summa - (self.price.summa * self.discount/100)
        return s * self.count

    @property
    def NDS(self):
        n = self.price.NDS - (self.price.NDS * self.discount/100)
        return n * self.count

###

class Contract(models.Model):
    """ Договор """
    DOCUMENT_TYPE = 'contract'
    STATE_CREATED = 1
    STATE_SIGNED  = 2
    STATE_CLOSED  = 3
    STATE_REMOVED = 4
    STATE_CHOICES = (
            (STATE_CREATED, _('Created')),
            (STATE_SIGNED,  _('Signed')),
            (STATE_CLOSED,  _('Closed')),
            (STATE_REMOVED, _('Removed')),
        )
    SELECT_WORK = [1,2]

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
            User,
            verbose_name=_('user'))
    supplier = models.ForeignKey(
            Org,
            limit_choices_to={'is_active': True},
            null=True, blank=True,
            verbose_name=_('supplier'))
    client = models.ForeignKey(
            Client,
            null=True, blank=True,
            verbose_name=_('client'))
    state = models.IntegerField(
            choices=STATE_CHOICES,
            default=STATE_CREATED,
            verbose_name = _('state'))
    date = models.DateField(
            null=True, blank=True,
            verbose_name=_('date'))
    template = models.ForeignKey(
            Template,
            blank=True, null=True,
            verbose_name=_('template'))
    comment = models.TextField(
            blank=True,
            verbose_name=_('comment'))
    class Meta:
        ordering = ['-id']
        verbose_name = _('contract')
        verbose_name_plural = _('contracts')
        get_latest_by = 'date'

    def __unicode__(self):
        return _('Contract %(num)s of %(date)s') % {
            'num': unicode(self.id),
            'date': self.date.strftime("%d.%m.%Y")
            }

class Invoice(models.Model):
    """ Счёт """
    DOCUMENT_TYPE = 'invoice'
    STATE_CREATED = 1
    STATE_ADVANCE = 2
    STATE_PAID    = 3
    STATE_REMOVED = 4
    STATE_CHOICES = (
            (STATE_CREATED, _('Created')),
            (STATE_ADVANCE, _('Advance')),
            (STATE_PAID,    _('Paid')),
            (STATE_REMOVED, _('Removed')),
        )
    SELECT_WORK = [1,2,3]
    SELECT_CASH = [2,3]

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
            User,
            verbose_name=_('user'))
    contract = models.ForeignKey(
            Contract,
            null=True, blank=True,
            verbose_name=_('contract'))
    supplier = models.ForeignKey(
            Org,
            limit_choices_to={'is_active': True},
            null=True, blank=True,
            verbose_name=_('supplier'))
    client = models.ForeignKey(
            Client,
            null=True, blank=True,
            verbose_name=_('client'))
    state = models.IntegerField(
            choices=STATE_CHOICES,
            default=STATE_CREATED,
            verbose_name = _('state'))
    date = models.DateField(
            null=True, blank=True,
            verbose_name=_('date'))
    comment = models.TextField(
            blank=True,
            verbose_name=_('comment'))
    specs = models.ManyToManyField(
            Spec,
            null=True, blank=True,
            verbose_name = _('specifications'))

    def __unicode__(self):
        return _('Invoice %(id)s of %(date)s') % {
            'id': unicode(self.id),
            'date': self.date.strftime("%d.%m.%Y")
            }

    class Meta:
        ordering = ['user', '-created',]
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
        get_latest_by = 'date'

    def save(self, **kwargs):
        super(Invoice, self).save(**kwargs)

    def delete(self, **kwargs):
        self.state = STATE_REMOVED
        self.save()

    @property
    def summa(self):
        return sum([ x.summa for x in self.specs.all()])

    @property
    def NDS(self):
        return sum([ x.NDS for x in self.specs.all()])

    @property
    def state_created(self):
        return self.state == STATE_CREATED
    @property
    def state_paid(self):
        return self.state == STATE_PAID
    @property
    def state_advance(self):
        return self.state == STATE_ADVANCE

    @property
    def payment(self):
        return sum([ x.summa for x in self.payment_set.filter(is_paid=True) ])
    @property
    def payment_cash(self):
        return sum([ x.summa for x in self.payment_set.filter(is_paid=True, payment=Payment.KIND_CASH) ])
    @property
    def payment_cashless(self):
        return sum([ x.summa for x in self.payment_set.filter(is_paid=True, payment=Payment.KIND_CASHLESS) ])
    @property
    def payment_card(self):
        return sum([ x.summa for x in self.payment_set.filter(is_paid=True, payment=Payment.KIND_CARD) ])
    @property
    def debet(self):
        return float(self.summa) - float(self.payment)

class Payment(models.Model):
    """ Приходный ордер """
    DOCUMENT_TYPE = 'payment'
    KIND_CASH      = 1
    KIND_CASHLESS  = 2
    KIND_CARD      = 3
    KIND_CHOICES = (
            (KIND_CASH,     _('Cash')),
            (KIND_CASHLESS, _('Cashless')),
            (KIND_CARD,     _('Card')),
        )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
            User,
            verbose_name=_('user'))
    kind = models.IntegerField(
            choices=KIND_CHOICES,
            default=KIND_CASH,
            verbose_name=_('kind of payment'))
    invoice = models.ForeignKey(
            Invoice,
            verbose_name=('invoice'))
    summa = models.DecimalField(
            max_digits=10, decimal_places=2,
            default=0.0,
            verbose_name=('summa'))
    comment = models.TextField(
            blank=True,
            verbose_name=_('comment'))
    is_paid = models.BooleanField(
            default=False,
            verbose_name=_('confirm'))

    def __unicode__(self):
        return _('Payment %(id)s of invoice %(invoice)s of %(date)s') % {
            'id': unicode(self.id),
            'invoice': unicode(self.invoice.id),
            'date': self.invoice.date.strftime("%d.%m.%Y"),
            }

    class Meta:
        ordering = ['user', '-created',]
        verbose_name = _('payment')
        verbose_name_plural = _('payments')

    def save(self, **kwargs):
        if not self.summa:
            self.summa = str(self.invoice.debet)
        super(Payment, self).save(**kwargs)
        if self.is_paid:
            if float(self.summa) >= float(self.invoice.debet):
                self.invoice.state = Invoice.STATE_PAID
            else:
                self.invoice.state = Invoice.STATE_ADVANCE
            self.invoice.save()

    def delete(self, **kwargs):
        if self.is_paid:
            return False
        super(Payment, self).delete(**kwargs)

class Act(models.Model):
    """ Акт выполненных работ """
    DOCUMENT_TYPE = 'act'
    STATE_CREATED  = 1
    STATE_CLOSED   = 2
    STATE_REMOVED  = 3
    STATE_CHOICES = (
            (STATE_CREATED, _('Created')),
            (STATE_CLOSED,  _('Closed')),
            (STATE_REMOVED, _('Removed')),
        )
    SELECT_WORK = [1,2]

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
            User,
            verbose_name=_('user'))
    contract = models.ForeignKey(
            Contract,
            null=True, blank=True,
            verbose_name=_('contract'))
    invoice = models.ForeignKey(
            Invoice,
            null=True, blank=True,
            verbose_name=_('invoice'))
    state = models.IntegerField(
            choices=STATE_CHOICES,
            default=STATE_CREATED,
            verbose_name = _('state'))
    date = models.DateField(
            null=True, blank=True,
            verbose_name=_('date'))
    comment = models.TextField(
            blank=True,
            verbose_name=_('comment'))

    def __unicode__(self):
        return _('Act %(id)s of %(date)s') % {
            'id': unicode(self.id),
            'date': self.date.strftime("%d.%m.%Y"),
            }

    class Meta:
        ordering = ['user', '-created']
        verbose_name = _('act')
        verbose_name_plural = _('acts')

    def save(self, **kwargs):
        super(Act, self).save(**kwargs)

    def delete(self, **kwargs):
        self.state = STATE_REMOVED
        self.save()

    @property
    def summa(self):
        return sum([ x.summa for x in self.invoice.specs.all()])

    @property
    def NDS(self):
        return sum([ x.NDS for x in self.invoice.specs.all()])

    @property
    def state_created(self):
        return self.state == STATE_CREATED
    @property
    def state_closed(self):
        return self.state == STATE_CLOSED
