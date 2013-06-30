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
from django.utils.translation import ugettext_lazy as _
import datetime

from bwp.contrib.devices.remote import RemoteCommand

from dcon import ICP

class ICPi7000(object):
    is_remote = False

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote= True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.icp = ICP(*args, **kwargs)

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
            return bool(status[module])
        except:
            raise RuntimeError(unicode(_('Device is not responding.')))

    def off(self, module=1, channel=0):
        if self.is_remote:
            return self.remote("off", module=module, channel=channel)

        self.icp.off(module=module, channel=channel)
        status = self.status(module=module)
        try:
            return bool(not status[module])
        except:
            raise RuntimeError(unicode(_('Device is not responding.')))
