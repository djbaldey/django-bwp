# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/__bwp__.py
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
from bwp.sites import site
from bwp.models import ModelBWP, ManyToManyBWP
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group, User
from models import SpoolerDevice, LocalDevice, RemoteDevice, register


class UserCompose(ManyToManyBWP):
    model = User


class AdminUserCompose(ManyToManyBWP):
    model = User
    verbose_name = _('admin users')


class GroupCompose(ManyToManyBWP):
    model = Group


class AdminGroupCompose(ManyToManyBWP):
    model = Group
    verbose_name = _('admin groups')


class SpoolerDeviceCompose(ManyToManyBWP):
    model = SpoolerDevice
    list_display = ('state', 'method', 'group_hash', 'created', 'id')


class SpoolerDeviceAdmin(ModelBWP):
    list_display = (
        'local_device', 'state', 'method', 'group_hash', 'created', 'id',
    )
site.register(SpoolerDevice, SpoolerDeviceAdmin)


class LocalDeviceAdmin(ModelBWP):
    list_display = ('title', 'driver', 'port', 'username', 'id')
    search_fields = ['title']
    compositions = [
        ('users', UserCompose),
        ('groups', GroupCompose),
        ('admin_users', AdminUserCompose),
        ('admin_groups', AdminGroupCompose),
        ('spoolerdevice_set', SpoolerDeviceCompose),
    ]
site.register(LocalDevice, LocalDeviceAdmin)


class RemoteDeviceAdmin(ModelBWP):
    list_display = ('title', 'driver', 'remote_url', 'remote_id', 'username',
                    'id')
    search_fields = ['title']
    compositions = [
        ('users', UserCompose),
        ('groups', GroupCompose),
        ('admin_users', AdminUserCompose),
        ('admin_groups', AdminGroupCompose),
    ]
site.register(RemoteDevice, RemoteDeviceAdmin)

# Регистрация регистра устройств
site.devices = register
