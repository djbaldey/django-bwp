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

from bwp import User
from bwp.db import managers, fields
from bwp.utils.classes import upload_to
from bwp.contrib.abstracts.models import AbstractOrg, AbstractPerson, AbstractGroupUnique

class Person(AbstractPerson):
    """ Персоналии """
    user = models.ForeignKey(
            User,
            null=True, blank=True,
            verbose_name = _('user'))
    photo = models.ImageField(upload_to=upload_to,
            null=True, blank=True,
            verbose_name=_('photo'))

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name']
        verbose_name = _('person')
        verbose_name_plural = _('persons')

    @property
    def image(self):
        return self.photo.image

class Org(AbstractOrg):
    """ Организации """
    is_supplier = models.BooleanField(
            default=False,
            verbose_name = _("is supplier"))
    is_active = models.BooleanField(
            default=True,
            verbose_name = _("is active"))

    admin_objects = models.Manager()
    objects = managers.ActiveManager()

    class Meta:
        verbose_name = _("org")
        verbose_name_plural = _("orgs")
        unique_together = ('inn',)
