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
from bwp.contrib.abstracts.models import AbstractGroup

class Country(AbstractGroup):
    """ ОКСМ — Общероссийский классификатор стран мира """
    code = models.CharField(
            max_length=3,
            primary_key=True,
            verbose_name = _('code'))
    code_s2 = models.CharField(
            max_length=2,
            unique=True,
            verbose_name = _('code 2 symbol'))
    code_s3 = models.CharField(
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
    """ Валюты """
    country = models.ForeignKey(
            Country,
            verbose_name = _('country'))
    code = models.CharField(
            max_length=3, blank=True,
            verbose_name = _('code'))
    class Meta:
        ordering = ['title',]
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
