# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/drivers/ICPDAS/__init__.py
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
from django.utils.translation import ugettext_lazy as _

from bwp.contrib.devices.remote import RemoteCommand

from .dcon import ICP, ICPDummy, ICPError


class ICPi7000(object):
    is_remote = False
    driver = ICP

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote = True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.icp = self.driver(*args, **kwargs)

    def status(self, module=1):
        if self.is_remote:
            return self.remote("status", module=module)

        return self.icp.status(module=module)

    def on(self, module=1, channel=0):
        if self.is_remote:
            return self.remote("on", module=module, channel=channel)

        self.icp.on(module=module, channel=channel)
        status = self.status(module=module)
        try:
            return bool(status[channel])
        except:
            raise ICPError(_('Device is not responding.'))

    def off(self, module=1, channel=0):
        if self.is_remote:
            return self.remote("off", module=module, channel=channel)

        self.icp.off(module=module, channel=channel)
        status = self.status(module=module)
        try:
            return bool(not status[channel])
        except:
            raise ICPError(_('Device is not responding.'))


class ICPi7000Dummy(ICPi7000):
    driver = ICPDummy
