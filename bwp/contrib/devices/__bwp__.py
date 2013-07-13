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
from bwp.sites import site
from bwp.models import ModelBWP, ManyToManyBWP
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group, User
from models import *


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
    list_display = ('state', 'method', 'group_hash', 'id')

class SpoolerDeviceAdmin(ModelBWP):
    list_display = ('local_device', 'state', 'method', 'group_hash', 'id')

site.register(SpoolerDevice, SpoolerDeviceAdmin)

class LocalDeviceAdmin(ModelBWP):
    list_display = ('title', 'driver', 'port', 'username', 'id')
    search_fields = ['title', ]
    compositions = [
        ('users', UserCompose),
        ('groups', GroupCompose),
        ('admin_users', AdminUserCompose),
        ('admin_groups', AdminGroupCompose),
        ('spoolerdevice_set', SpoolerDeviceCompose),
    ]

site.register(LocalDevice, LocalDeviceAdmin)

class RemoteDeviceAdmin(ModelBWP):
    list_display = ('title', 'driver', 'remote_url', 'remote_id', 'username', 'id')
    search_fields = ['title', ]
    compositions = [
        ('users', UserCompose),
        ('groups', GroupCompose),
        ('admin_users', AdminUserCompose),
        ('admin_groups', AdminGroupCompose),
    ]

site.register(RemoteDevice, RemoteDeviceAdmin)

site.devices = register
