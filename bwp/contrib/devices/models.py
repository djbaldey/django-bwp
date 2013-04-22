# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2013 Grigoriy Kramarenko.
###############################################################################
# This file is part of Bizon-RC.
#
#    Bizon-RC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Bizon-RC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Bizon-RC.  If not, see <http://www.gnu.org/licenses/>.
#
# Этот файл — часть Bizon-RC.
#
#   Bizon-RC - свободная программа: вы можете перераспространять ее и/или
#   изменять ее на условиях Стандартной общественной лицензии GNU в том виде,
#   в каком она была опубликована Фондом свободного программного обеспечения;
#   либо версии 3 лицензии, либо (по вашему выбору) любой более поздней
#   версии.
#
#   Bizon-RC распространяется в надежде, что она будет полезной,
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
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from bwp.contrib.abstracts.models import AbstractGroupUnique

from drivers import DRIVER_CLASSES

class Register(object):
    """ Класс-регистратор устройств """

    @property
    def devices(self):
        if not getattr(self, '_device'):
            self.load()
        return self._devices

    def load(self):
        self._devices = [ x for x in Device.objects.all() ]

register = Register()

class Device(AbstractGroupUnique):
    """ Устройство """
    DRIVER_CHOICES = [ (x, x) for x in DRIVER_CLASSES.keys() ]
    BOD_CHOICES = (
        (None, _('nothing')),
        (2400,   '2400'),
        (4800,   '4800'),
        (9600,   '9600'),
        (19200,  '19200'),
        (38400,  '38400'),
        (57600,  '57600'),
        (115200, '115200'),
    )
    driver = models.CharField(
            choices=DRIVER_CHOICES,
            max_length=255,
            verbose_name = _('driver'))
    port = models.CharField(
            max_length=50,
            unique=True,
            verbose_name = _('port'))
    username = models.CharField(
            max_length=100,
            blank=True,
            verbose_name = _('username'))
    password = models.CharField(
            max_length=100,
            blank=True,
            verbose_name = _('password'))
    admin_password = models.CharField(
            max_length=100,
            blank=True,
            verbose_name = _('admin password'))
    bod = models.IntegerField(
            choices=BOD_CHOICES,
            null=True,
            default=None,
            verbose_name = _('bod'))

    users = models.ManyToManyField(
            User,
            null=True, blank=True,
            related_name='user_device_set',
            verbose_name=_('users'))

    groups = models.ManyToManyField(
            Group,
            null=True, blank=True,
            related_name='group_device_set',
            verbose_name=_('groups'))

    admin_users = models.ManyToManyField(
            User,
            null=True, blank=True,
            related_name='admin_user_device_set',
            verbose_name=_('admin users'))

    admin_groups = models.ManyToManyField(
            Group,
            null=True, blank=True,
            related_name='admin_group_device_set',
            verbose_name=_('admin groups'))

    class Meta:
        verbose_name = _('device')
        verbose_name_plural = _('devices')

    @property
    def device(self):
        """ Свойство возвращает экземпляр управляющего класса устройства
            со всеми его методами
        """
        if not getattr(self, '_device'):
            cls = DRIVER_CLASSES[self.driver]
            self._device = cls(
                port=self.port,
                username=self.username,
                password=self.password,
                admin_password=self.admin_password,
                bod=self.bod, 
            )
        return self._device

    def has_permission(self, request, **kwargs):
        """ Проверка прав на использование устройства """
        user = request.user
        if user in self.users.all():
            return True
        elif set(user.group_set.all()).intersection(set(self.groups.all())):
            return True
        return False

    def has_admin_permission(self, request, **kwargs):
        """ Проверка прав на использование устройства с правами
            администратора
        """
        user = request.user
        if user in self.admin_users.all():
            return True
        elif set(user.admin_group_set.all()).intersection(set(self.admin_groups.all())):
            return True
        return False

    def save(self, **kwargs):
        super(Device, self).save(**kwargs)
        register.load()

    def delete(self, **kwargs):
        super(Device, self).delete(**kwargs)
        register.load()

