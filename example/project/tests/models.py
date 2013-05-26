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
from bwp.contrib.abstracts.models import *

class Group(AbstractGroup):
    """ Test AbstractGroup model """
    class Meta:
        ordering = ['title',]
        verbose_name = _('group')
        verbose_name_plural = _('groups')

class GroupUnique(AbstractGroupUnique):
    """ Test AbstractGroupUnique model """
    class Meta:
        ordering = ['title',]
        verbose_name = _('unique group')
        verbose_name_plural = _('unique groups')

class Org(AbstractOrg):
    """ Test AbstractOrg model """
    group = models.ForeignKey(
            Group,
            blank=True, null=True,
            verbose_name = _('group'))
    groupunique = models.ForeignKey(
            GroupUnique,
            blank=True, null=True,
            verbose_name = _('unique group'))
    class Meta:
        ordering = ['title',]
        verbose_name = _('org')
        verbose_name_plural = _('orgs')

    @property
    def get_group(self):
        return self.group

    @property
    def get_groupunique(self):
        return self.groupunique

class Person(AbstractPerson):
    """ Test AbstractPerson model """
    group = models.ForeignKey(
            Group,
            blank=True, null=True,
            verbose_name = _('group'))
    groupunique = models.ForeignKey(
            GroupUnique,
            blank=True, null=True,
            verbose_name = _('unique group'))
    orgs = models.ManyToManyField(
            Org,
            blank=True, null=True,
            verbose_name = _('orgs'))
    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name']
        verbose_name = _('person')
        verbose_name_plural = _('persons')

class VideoCode(AbstractVideoCode):
    """ Test AbstractVideoCode model """
    group = models.ForeignKey(
            Group,
            blank=True, null=True,
            verbose_name = _('group'))
    groupunique = models.ForeignKey(
            GroupUnique,
            blank=True, null=True,
            verbose_name = _('unique group'))
    class Meta:
        ordering = ['pk',]
        verbose_name = _('code')
        verbose_name_plural = _('video')

class Image(AbstractImage):
    """ Test AbstractImage model """
    group = models.ForeignKey(
            Group,
            blank=True, null=True,
            verbose_name = _('group'))
    groupunique = models.ForeignKey(
            GroupUnique,
            blank=True, null=True,
            verbose_name = _('unique group'))
    class Meta:
        ordering = ['pk',]
        verbose_name = _('image')
        verbose_name_plural = _('images')

class File(AbstractFile):
    """ Test AbstractFile model """
    group = models.ForeignKey(
            Group,
            blank=True, null=True,
            verbose_name = _('group'))
    groupunique = models.ForeignKey(
            GroupUnique,
            blank=True, null=True,
            verbose_name = _('unique group'))
    class Meta:
        ordering = ['pk',]
        verbose_name = _('file')
        verbose_name_plural = _('files')
