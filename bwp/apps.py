# -*- coding: utf-8 -*-
#
#   Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
#
#   This file is part of BWP.
#
#   BWP is free software: you can redistribute it and/or
#   modify it under the terms of the GNU Affero General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   BWP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public
#   License along with BWP. If not, see
#   <http://www.gnu.org/licenses/>.
#

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class BwpConfig(AppConfig):
    name = 'bwp'
    verbose_name = _('Platform')

    def ready(self):
        super(BwpConfig, self).ready()
        from bwp.sites import autodiscover
        autodiscover()
