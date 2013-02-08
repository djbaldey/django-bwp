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
from bwp.contrib.contacts.models import Person, Org
from bwp.db import fields
from bwp.conf import settings

class AbstractUserSettings(models.Model):
    """ Общая модель """
    person = models.ForeignKey(
            Person,
            limit_choices_to={'user__isnull': False},
            verbose_name=_('person'))
    json = fields.JSONField(
            blank=True,
            verbose_name = _('JSON value'))

    def __unicode__(self):
        return unicode(self.person)

    class Meta:
        abstract = True

    @property
    def value(self):
        return self.json

class GlobalUserSettings(AbstractUserSettings):
    """ Глобальные настройки пользователей """
    class Meta:
        ordering = ['person',]
        verbose_name = _('global settings')
        verbose_name_plural = _('global settings')
        unique_together = ('person',)

class UserSettings(AbstractUserSettings):
    """ Настройки пользователей для каждой организации из
        зарегистрированных как поставщик.
    """
    org = models.ForeignKey(
            Org,
            null=True, blank=True,
            limit_choices_to={'is_supplier': True, 'is_active': True},
            verbose_name=_('org'))

    class Meta:
        ordering = ['person', 'org',]
        verbose_name = _('settings')
        verbose_name_plural = _('settings')
        unique_together = ('person', 'org',)

