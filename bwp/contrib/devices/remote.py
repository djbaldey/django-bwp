# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/remote.py
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
import os
import ssl
from tempfile import NamedTemporaryFile

from quickapi.client import BaseClient
# from quickapi.client import RemoteAPIError  # NOQA

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass


class Client(BaseClient):
    """ Соединение с удалённым API, где расположено устройство """

    timeout = 60000

    def __init__(self, device=None, **kwargs):
        """ Инициализация """
        if device and hasattr(device, 'cookies'):
            if not device.cookies or not os.path.exists(device.cookies):
                f = NamedTemporaryFile(delete=False)
                device.cookies = f.name
                device.save()
                f.close()
            kwargs['cookie_filename'] = device.cookies
        super(Client, self).__init__(**kwargs)


class RemoteCommand(object):
    """ Выполнение команды на удалённом устройстве """

    def __init__(self, remote_url, remote_id, device=None, **kwargs):
        self.remote_url = remote_url
        self.remote_id = remote_id
        self.api = Client(url=self.remote_url, device=device, **kwargs)

    def __call__(self, command, *args, **kwargs):
        if args:
            raise ValueError('Support only named arguments.')
        return self.api.method(
            'device_command', device=self.remote_id, command=command,
            params=kwargs
        )
