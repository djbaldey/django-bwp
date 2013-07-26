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

import json, urllib, base64, traceback

class BaseAPI(object):
    """ Соединение с удалённым API, где расположено устройство """

    username = 'admin'
    password = 'admin'
    url      = 'http://localhost:8000/api/'
    timeout  = 60000
    error    = None

    def __init__(self, **kwargs):
        """ Инициализация """
        for key, val in kwargs.items():
            setattr(self, key, val)

    @property
    def format_error(self):
        """ Выводит ошибку в презентабельном виде """
        return unicode(traceback.format_exc(self.error))

    def get_request(self, data, **kwargs):
        """ Возвращает новый объект запроса. """
        params = urllib.urlencode({'jsonData': data})
        return urllib.urlopen(url=self.url, data=params)

    def get_result(self, data, **kwargs):
        """ Запрашивает данные из API """
        jsondata = json.dumps(data, ensure_ascii=True)
        try:
            jsondata = jsondata.encode('utf-8')
        except:
            pass
        request = self.get_request(jsondata)
        try:
            data = request.read()
        except Exception as e:
            self.error = e
            print self.format_error
            data = None
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
            print repr(msg)
            try:
                msg = msg.encode('utf-8')
            except:
                pass
            print 'RemoteCommand:', msg
            raise RuntimeError(msg)
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
    def __init__(self, remote_url, remote_id, **kwargs):
        self.remote_url = remote_url
        self.device     = remote_id
        self.api        = BaseAPI(url=remote_url, **kwargs)

    def __call__(self, command, *args, **kwargs):
        if args:
            raise ValueError('Support only named arguments.')

        return self.api.method('device_command', device=self.device,
                                command=command, params=kwargs)

