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
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from bwp.contrib.abstracts.models import AbstractGroup
from bwp.db import fields
import hashlib, datetime

from drivers import DRIVER_CLASSES

class Register(object):
    """ Класс-регистратор локальных устройств """

    def __iter__(self):
        return self.devices

    @property
    def devices(self):
        if not hasattr(self, '_devices'):
            self.load()
        return self._devices

    def load(self):
        self._devices = dict([
            (x.pk, x) for x in LocalDevice.objects.all()
        ])
        return self._devices
    
    def get_devices(self, request=None):
        data = {}
        if request:
            for pk, x in self.devices.items():
                if x.has_permission(request) or x.has_admin_permission(request):
                    data[pk] = x
        else:
            for pk, x in self.devices.items():
                data[pk] = x
        return data
    
    def get_list(self, request):
        data = []
        for x in self.get_devices(request).values():
            data.append(x.values('pk', 'title', 'driver'))
        return data

register = Register()

class BaseDevice(AbstractGroup):
    """ Базовый класс локального или удалённого устройства """
    DRIVER_CHOICES = [ (x, x) for x in DRIVER_CLASSES.keys() ]
    driver = models.CharField(
            choices=DRIVER_CHOICES,
            max_length=255,
            verbose_name = _('driver'))

    users = models.ManyToManyField(
            User,
            null=True, blank=True,
            related_name='user_%s_set',
            verbose_name=_('users'))

    groups = models.ManyToManyField(
            Group,
            null=True, blank=True,
            related_name='group_%s_set',
            verbose_name=_('groups'))

    admin_users = models.ManyToManyField(
            User,
            null=True, blank=True,
            related_name='admin_user_%s_set',
            verbose_name=_('admin users'))

    admin_groups = models.ManyToManyField(
            Group,
            null=True, blank=True,
            related_name='admin_group_%s_set',
            verbose_name=_('admin groups'))

    username = models.CharField(
            max_length=100,
            blank=True,
            verbose_name = _('username'))
    password = models.CharField(
            max_length=100,
            blank=True,
            verbose_name = _('password'))

    class Meta:
        abstract = True

    def has_permission(self, request, **kwargs):
        """ Проверка прав на использование устройства.
            Разрешено по-умолчанию, когда везде пусто.
        """

        if not self.users.count() and not self.groups.count():
            return True

        user = request.user
        if user in self.users.all():
            return True
        elif set(user.group_set.all()).intersection(set(self.groups.all())):
            return True
        return False

    def has_admin_permission(self, request, **kwargs):
        """ Проверка прав на использование устройства с правами
            администратора.
            
            Запрещено по-умолчанию, когда везде пусто.
        """
        user = request.user
        if user in self.admin_users.all():
            return True
        elif set(user.admin_group_set.all()).intersection(set(self.admin_groups.all())):
            return True
        return False

    @property
    def device(self):
        """ Свойство возвращает экземпляр управляющего класса устройства
            со всеми его методами
        """
        if not getattr(self, '_device', None):
            cls = DRIVER_CLASSES[self.driver]
            if not self.remote and hasattr(cls, 'SpoolerDevice'):
                cls.SpoolerDevice = SpoolerDevice
                cls.local_device = self

            D = {'remote': self.remote }
            if hasattr(self, 'username') and self.username:
                D['username'] = self.username
            if hasattr(self, 'password') and self.password:
                D['password'] = self.password
            if hasattr(self, 'admin_password') and self.admin_password:
                D['admin_password'] = self.admin_password

            if hasattr(self, 'port') and self.port:
                D['port'] = self.port
            if hasattr(self, 'remote_url') and self.remote_url:
                D['remote_url'] = self.remote_url
            if hasattr(self, 'remote_id') and self.remote_id:
                D['remote_id'] = self.remote_id
            if hasattr(self, 'config') and self.config:
                config = self.config or {}
                D.update(config)

            self._device = cls(**D)

        return self._device

class LocalDevice(BaseDevice):
    """ Локальное устройство """
    remote = False

    port = models.CharField(
            max_length=50,
            blank=True,
            verbose_name = _('port'))

    config = fields.JSONField(
            default={}, blank=True,
            verbose_name = _('config'))

    admin_password = models.CharField(
            max_length=100,
            blank=True,
            verbose_name = _('admin password'))

    class Meta:
        ordering = ['title']
        verbose_name = _('local device')
        verbose_name_plural = _('local devices')

    def save(self, **kwargs):
        super(LocalDevice, self).save(**kwargs)
        register.load()

    def delete(self, **kwargs):
        super(LocalDevice, self).delete(**kwargs)
        register.load()

class RemoteDevice(BaseDevice):
    """ Удалённое устройство """
    remote = True

    remote_url = models.CharField(
            max_length=200,
            verbose_name = _('url'))
    remote_id = models.IntegerField(
            verbose_name = _('identifier'))

    class Meta:
        ordering = ['title']
        verbose_name = _('remote device')
        verbose_name_plural = _('remote devices')
        unique_together = ('remote_url', 'remote_id')

class SpoolerDevice(models.Model):
    """ Диспетчер очереди команд для устройств """
    created = models.DateTimeField(
            auto_now_add=True,
            verbose_name=_('created'))
    updated = models.DateTimeField(
            auto_now=True,
            verbose_name=_('updated'))

    STATE_WAITING = 1
    STATE_ERROR = 2
    STATE_CHOICES = (
        (STATE_WAITING, _('waiting')),
        (STATE_ERROR,   _('error')),
    )

    state = models.IntegerField(
            choices=STATE_CHOICES,
            default=1,
            verbose_name = _('state'))
    local_device = models.ForeignKey(
            LocalDevice,
            verbose_name = _('local device'))
    method = models.CharField(
            max_length=50,
            verbose_name = _('method'))
    kwargs = fields.JSONField(
            default={}, blank=True,
            verbose_name = _('config'))
    group_hash = models.CharField(
            max_length=32,
            blank=True,
            verbose_name = _('method'))

    def __unicode__(self):
        return unicode(self.local_device)

    class Meta:
        ordering = ['pk']
        verbose_name = _('spooler device')
        verbose_name_plural = _('spooler device')

    def generate_hash(self):
        md5 = hashlib.md5()
        md5.update(str(self.local_device.pk))
        md5.update(self.method)
        md5.update(str(self.created or datetime.datetime.now()))
        return md5.hexdigest()

    def save(self, **kwargs):
        if not self.group_hash:
            self.group_hash = self.generate_hash()
        super(SpoolerDevice, self).save(**kwargs)
