# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
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
from bwp.contrib.abstracts.models import AbstractGroup, AbstractGroupText

class Country(AbstractGroup):
    """ Общероссийский классификатор стран мира (ОКСМ) """
    code = models.CharField(
            max_length=3,
            primary_key=True,
            verbose_name = _('code'))
    symbol2 = models.CharField(
            max_length=2,
            unique=True,
            verbose_name = _('code 2 symbol'))
    symbol3 = models.CharField(
            max_length=3,
            unique=True,
            verbose_name = _('code 3 symbol'))
    full_title = models.CharField(
            max_length=512,
            blank=True,
            verbose_name = _('full title'))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title',]
        verbose_name = _('country')
        verbose_name_plural = _('countries')

class Currency(AbstractGroup):
    """ Общероссийский классификатор валют (ОКB) """
    code = models.CharField(
            max_length=3,
            primary_key=True,
            verbose_name = _('code'))
    symbol3 = models.CharField(
            max_length=3,
            unique=True,
            verbose_name = _('code 3 symbol'))
    countries = models.ManyToManyField(
            Country,
            blank=True,
            verbose_name = _('countries'))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title',]
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
    code = models.CharField(
            max_length=7,
            primary_key=True,
            verbose_name = _('code'))
    control = models.SmallIntegerField(
            null=True, blank=True,
            verbose_name = _('control number'))
    parent = models.ForeignKey(
            "Document",
            null=True, blank=True,
            verbose_name = _('document parent'))
    document_index = models.CharField(
            max_length=64,
            blank=True, null=True,
            verbose_name = _('document index'))
    period = models.CharField(
            max_length=128,
            blank=True, null=True,
            verbose_name = _('periodic'))

    class Meta:
        ordering = ['title',]
        verbose_name = _('document')
        verbose_name_plural = _('documents')

class MeasureUnitCategory(AbstractGroup):
    class Meta:
        ordering = ['title',]
        verbose_name = _('category')
        verbose_name_plural = _('categories of measure units')

class MeasureUnitGroup(AbstractGroup):
    class Meta:
        ordering = ['title',]
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
    code = models.CharField(
            max_length=3,
            primary_key=True,
            verbose_name = _('code'))
    note_ru = models.CharField(
            max_length=50,
            blank=True, null=True,
            verbose_name = _('RU'),
            help_text = _('notation RU'))
    note_iso = models.CharField(
            max_length=50,
            blank=True, null=True,
            verbose_name = _('ISO'),
            help_text = _('notation ISO'))
    symbol_ru = models.CharField(
            max_length=50,
            blank=True, null=True,
            verbose_name = _('symbol RU'),
            help_text = _('symbolic notation RU'))
    symbol_iso = models.CharField(
            max_length=50,
            blank=True, null=True,
            verbose_name = _('symbol ISO'),
            help_text = _('symbolic notation ISO'))
    category = models.ForeignKey(
            MeasureUnitCategory,
            null=True, blank=True,
            verbose_name = _('category'))
    group = models.ForeignKey(
            MeasureUnitGroup,
            null=True, blank=True,
            verbose_name = _('group'))

    class Meta:
        ordering = ['title',]
        verbose_name = _('unit')
        verbose_name_plural = _('measure units')
