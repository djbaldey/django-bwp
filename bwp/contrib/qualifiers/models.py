# -*- coding: utf-8 -*-
#
#  bwp/contrib/qualifiers/models.py
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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from bwp.contrib.abstracts.models import AbstractGroup, AbstractGroupText


class Country(AbstractGroup):
    """ Общероссийский классификатор стран мира (ОКСМ) """
    code = models.CharField(_('code'), max_length=3, primary_key=True)
    symbol2 = models.CharField(_('code 2 symbol'), max_length=2, unique=True)
    symbol3 = models.CharField(_('code 3 symbol'), max_length=3, unique=True)
    full_title = models.CharField(_('full title'), max_length=512, blank=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('country')
        verbose_name_plural = _('countries')


class Currency(AbstractGroup):
    """ Общероссийский классификатор валют (ОКB) """
    code = models.CharField(_('code'), max_length=3, primary_key=True)
    symbol3 = models.CharField(_('code 3 symbol'), max_length=3, unique=True)
    countries = models.ManyToManyField(Country, blank=True,
                                       verbose_name=_('countries'))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')


class Document(AbstractGroupText):
    """ Общероссийский классификатор управленческой документации (ОКУД)
        является составной частью Единой системы классификации и
        кодирования технико-экономической и социальной информации
        и охватывает унифицированные системы документации и формы
        документов, разрешенных к применению в народном хозяйстве.

        ОКУД предназначен для решения следующих задач:
        - регистрации форм документов;
        - упорядочения информационных потоков в народном хозяйстве;
        - сокращения количества применяемых форм;
        - исключения из обращения неунифицированных форм документов;
        - обеспечения учета и систематизации унифицированных форм
          документов на основе их регистрации;
        - контроля за составом форм документов и исключения дублирования
          информации, применяемой в сфере управления;
        - рациональной организации контроля за применением
          унифицированных форм документов.

        Объектами классификации в ОКУД являются общероссийские
        (межотраслевые, межведомственные) унифицированные формы
        документов, утверждаемые министерствами (ведомствами) Российской
        Федерации — разработчиками унифицированных систем документации
        (УСД).
    """
    code = models.CharField(_('code'), max_length=7, primary_key=True)
    control = models.SmallIntegerField(_('control number'),
                                       null=True, blank=True)
    parent = models.ForeignKey("Document", null=True, blank=True,
                               verbose_name=_('document parent'))
    document_index = models.CharField(_('document index'), max_length=64,
                                      blank=True, null=True)
    period = models.CharField(_('periodic'), max_length=128,
                              blank=True, null=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('document')
        verbose_name_plural = _('documents')


class MeasureUnitCategory(AbstractGroup):
    class Meta:
        ordering = ['title']
        verbose_name = _('category')
        verbose_name_plural = _('categories of measure units')


class MeasureUnitGroup(AbstractGroup):
    class Meta:
        ordering = ['title']
        verbose_name = _('group')
        verbose_name_plural = _('groups of measure units')


class MeasureUnit(AbstractGroup):
    """ Общероссийский классификатор единиц измерения (ОКЕИ)
        используется при количественной оценке социальных, технических и
        экономических показателей, в частности, в целях ведения
        государственного учета. Классификатор входит в состав Единой
        системы классификации и кодирования технико-экономической и
        социальной информации РФ (ЕСКК). Коды ОКЕИ были введены на
        территории РФ взамен Общесоюзного классификатора «Система
        обозначений единиц измерения, используемых в АСУ».

        Коды ОКЕИ разработаны на основе международной классификации
        единиц измерения Европейской экономической комиссии Организации
        Объединенных Наций (ЕЭК ООН) «Коды для единиц измерения,
        используемых в международной торговле» (Рекомендация N 20
        Рабочей группы по упрощению процедур международной торговли
        (РГ 4) ЕЭК ООН — далее Рекомендация N 20 РГ 4 ЕЭК ООН), Товарной
        номенклатуры внешнеэкономической деятельности (ТН ВЭД) в части
        используемых единиц измерения и с учетом требований
        международных стандартов ИСО 31/0-92 «Величины и единицы
        измерения. Часть 0. Общие принципы» и ИСО 1000-92 «Единицы СИ и
        рекомендации по применению кратных единиц и некоторых других
        единиц».

        Классификатор единиц измерения ОКЕИ увязан с ГОСТ 8.417-81
        «Государственная система обеспечения единства измерений.
        Единицы физических величин».

        Данный классификатор единиц изменения широко используется при
        прогнозировании финансовых показателей на макроуровне,
        используется для обеспечения международных статистических
        сопоставлений, осуществления внутренней и внешней торговли,
        государственного регулирования внешнеэкономической деятельности
        и организации таможенного контроля. Объектами классификации в
        ОКЕИ являются единицы измерения, используемые в этих сферах
        деятельности.
    """
    code = models.CharField(_('code'), max_length=3, primary_key=True)
    note_ru = models.CharField(_('RU'), max_length=50, blank=True, null=True,
                               help_text=_('notation RU'))
    note_iso = models.CharField(_('ISO'), max_length=50, blank=True, null=True,
                                help_text=_('notation ISO'))
    symbol_ru = models.CharField(_('symbol RU'), max_length=50,
                                 blank=True, null=True,
                                 help_text=_('symbolic notation RU'))
    symbol_iso = models.CharField(_('symbol ISO'), max_length=50,
                                  blank=True, null=True,
                                  help_text=_('symbolic notation ISO'))
    category = models.ForeignKey(MeasureUnitCategory, null=True, blank=True,
                                 verbose_name=_('category'))
    group = models.ForeignKey(MeasureUnitGroup, null=True, blank=True,
                              verbose_name=_('group'))

    class Meta:
        ordering = ['title']
        verbose_name = _('unit')
        verbose_name_plural = _('measure units')
