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
import json, base64, traceback

from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils import six
from django.http import SimpleCookie

from quickapi.client import BaseClient

#~ if six.PY3:
    #~ from http.cookies import SimpleCookie
#~ else:
    #~ from Cookie import SimpleCookie

class DeviceCookie(SimpleCookie):
    """
    Класс для загрузки/сохранения куков в модель устройства.
    """
    def __init__(self, device, **kwargs):
        """ Инициализация """
        self.device = device
        super(DeviceCookie, self).__init__(**kwargs)

    def load(self):
        """ Загрузка из модели """
        cookies = self.device.cookies
        if not six.PY3:
            cookies = cookies.encode('utf-8')
        super(DeviceCookie, self).load(s)

    def save(self, **kwargs):
        """ Сохранение изменённых куков в модель """
        cookies = self.output()
        if self.device.cookies != cookies:
            self.device.cookies = cookies
            self.device.save()
    

class Client(BaseClient):
    """ Соединение с удалённым API, где расположено устройство """

    timeout  = 60000

    def __init__(self, device=None, **kwargs):
        """ Инициализация """
        self.device = device
        self.set_cookiejar(device)
        super(Client, self).__init__(**kwargs)

    def set_cookiejar(self, device):
        if device and hasattr(device, 'cookies'):
            self.cookiejar = DeviceCookie(device)
            self.cookiejar.load()


class RemoteCommand(object):
    """ Выполнение команды на удалённом устройстве """

    def __init__(self, remote_url, remote_id, device=None, **kwargs):
        self.remote_url = remote_url
        self.remote_id  = remote_id
        self.api = Client(url=self.remote_url, device=device, **kwargs)

    def __call__(self, command, *args, **kwargs):
        if args:
            raise ValueError('Support only named arguments.')

        return self.api.method('device_command',
                device=self.remote_id, command=command, params=kwargs)

