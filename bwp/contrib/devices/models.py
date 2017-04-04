# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/models.py
#
#  Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
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
from __future__ import unicode_literals
import hashlib
import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text, python_2_unicode_compatible

from bwp.contrib.abstracts.models import AbstractGroup
from bwp.db import fields

from .drivers import DRIVER_CLASSES


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
            data.append({
                'pk': x.pk,
                'title': x.title,
                'driver': x.driver
            })
        return data


register = Register()


class BaseDevice(AbstractGroup):
    """ Базовый класс локального или удалённого устройства """
    DRIVER_CHOICES = [(x, x) for x in DRIVER_CLASSES.keys()]
    driver = models.CharField(_('driver'), choices=DRIVER_CHOICES,
                              max_length=255)
    users = models.ManyToManyField(
        User, blank=True, related_name='user_%(class)s_set',
        verbose_name=_('users'),
    )
    groups = models.ManyToManyField(
        Group, blank=True, related_name='group_%(class)s_set',
        verbose_name=_('groups'),
    )
    admin_users = models.ManyToManyField(
        User, blank=True, related_name='admin_user_%(class)s_set',
        verbose_name=_('admin users'),
    )
    admin_groups = models.ManyToManyField(
        Group, blank=True,
        related_name='admin_group_%(class)s_set',
        verbose_name=_('admin groups'),
    )
    username = models.CharField(_('username'), max_length=100, blank=True)
    password = models.CharField(_('password'), max_length=100, blank=True)

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

            D = {'remote': self.remote}
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
            if hasattr(self, 'cookies'):
                D['device'] = self
            if hasattr(self, 'config') and self.config:
                config = self.config or {}
                D.update(config)

            self._device = cls(**D)
        return self._device


class LocalDevice(BaseDevice):
    """ Локальное устройство """
    remote = False

    port = models.CharField(_('port'), max_length=50, blank=True)
    config = fields.JSONField(_('config'), default={}, blank=True)
    admin_password = models.CharField(_('admin password'), max_length=100,
                                      blank=True)

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

    remote_url = models.CharField(_('url'), max_length=200)
    remote_id = models.IntegerField(_('identifier'))
    cookies = models.TextField(_('cookies'), blank=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('remote device')
        verbose_name_plural = _('remote devices')
        unique_together = ('remote_url', 'remote_id')


@python_2_unicode_compatible
class SpoolerDevice(models.Model):
    """ Диспетчер очереди команд для устройств """
    STATE_WAITING = 1
    STATE_ERROR = 2
    STATE_CHOICES = (
        (STATE_WAITING, _('waiting')),
        (STATE_ERROR, _('error')),
    )

    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    state = models.IntegerField(_('state'), choices=STATE_CHOICES, default=1)
    local_device = models.ForeignKey(LocalDevice,
                                     verbose_name=_('local device'))
    method = models.CharField(_('method'), max_length=50)
    kwargs = fields.JSONField(_('config'), default={}, blank=True)
    group_hash = models.CharField(_('method'), max_length=32, blank=True)

    def __str__(self):
        return force_text(self.local_device)

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
