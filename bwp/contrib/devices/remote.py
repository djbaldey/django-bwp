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

if six.PY3:
    from urllib.parse import urlencode
    from urllib.request import Request, build_opener, HTTPCookieProcessor
else:
    from urllib import urlencode
    from urllib2 import Request, build_opener, HTTPCookieProcessor

class AbstractError(Exception):
    message = ''
    def __init__(self, message=None, value=None):
        self.value   = value
        self.message = message or self.message

    def message_to_str(self):
        return force_text(self.message).encode('utf-8')

    def __str__(self):
        return self.message_to_str()

    def __repr__(self):
        if self.value is None:
            return repr(self.message_to_str())
        return repr(self.message_to_str(), self.value)

class APIReceiveError(AbstractError):
    message = _('Error in receiving data')

class APIUrlOpenError(AbstractError):
    message = _('The device does not respond, check the network connection.')


class BaseAPI(object):
    """ Соединение с удалённым API, где расположено устройство """

    username = 'admin'
    password = 'admin'
    url      = 'http://localhost:8000/api/'
    timeout  = 60000
    error    = None
    headers  = None

    def __init__(self, device=None, **kwargs):
        """ Инициализация """
        self.headers  = {
            "Content-type": "application/json",
            "Accept":       "application/json",
            "Cookie":       ""
        }

        self.device = device
        if hasattr(self.device, 'cookies'):
            self.headers["Cookies"] = self.device.cookies_string

        for key, val in kwargs.items():
            setattr(self, key, val)

    def get_request(self, data, **kwargs):
        """ Возвращает новый объект запроса. """

        params = urlencode({'jsonData': data})
        return Request(url=self.url, data=params, headers=self.headers)

    def get_response(self, request, openerargs=(), **kwargs):
        """
        Возвращает новый обработчик запроса и устанавливает куки.
        """

        cookiehand = HTTPCookieProcessor()
        opener = build_opener(cookiehand, *openerargs)
        try:
            response = opener.open(request, timeout=self.timeout)
        except IOError as e:
            raise APIUrlOpenError(value=self)

        if hasattr(self.device, 'cookies'):
            # Сохраняем изменённые куки в модель устройства
            cookies = cookiehand.cookiejar.make_cookies(response, request)
            cookies = '; '.join(['%s=%s' % (c.name, c.value) for c in cookies])
            if self.device.cookies != cookies:
                self.device.cookies = cookies
                self.device.save()

        return response

    def get_result(self, data, **kwargs):
        """ Запрашивает данные из API """
        jsondata = json.dumps(data, ensure_ascii=True)
        try:
            jsondata = jsondata.encode('utf8')
        except:
            pass

        request = self.get_request(jsondata)
        response = self.get_response(request)

        try:
            data = response.read()
        except Exception as e:
            print force_text(traceback.format_exc(e))
            raise e

        return data


    def json_loads(self, data, **kwargs):
        """ Переобразовывает JSON в объекты Python, учитывая кодирование"""
        try:
            data = json.loads(data.decode('zlib'))
        except:
            try:
                data = json.loads(data)
            except:
                data = None
        return data

    def prepare_data(self, data, **kwargs):
        """ Переопределяемый метод в наследуемых классах.
            Предварительно конвентирует отправляемые данные.
        """
        data['username'] = self.username 
        data['password'] = self.password 
        return data

    def clean(self, data, **kwargs):
        """ Преобразует полученные данные """
        data = self.json_loads(data)
        if data is None:
            return data
        status = data.get('status', None)
        if status != 200:
            msg = data.get('message')
            try:
                msg = force_text(msg)
            except:
                pass
            raise APIReceiveError(msg)
        return data['data']

    def method(self, method, **kwargs):
        """ Вызывает метод API и возвращает чистые данные """
        data = {'method': method, 'kwargs': kwargs}
        data = self.prepare_data(data)
        data = self.get_result(data)
        data = self.clean(data)
        return data

class RemoteCommand(object):
    """ Выполнение команды на удалённом устройстве """
    def __init__(self, remote_url, remote_id, model_device=None, **kwargs):
        self.remote_url = remote_url
        self.remote_id  = remote_id
        self.api = BaseAPI(url=self.remote_url, device=model_device, **kwargs)

    def __call__(self, command, *args, **kwargs):
        if args:
            raise ValueError('Support only named arguments.')

        return self.api.method('device_command',
                device=self.remote_id, command=command, params=kwargs)

