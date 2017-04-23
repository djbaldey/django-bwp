# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/drivers/ICPDAS/dcon.py
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
import serial
import time
from django.utils.translation import ugettext_lazy as _

from bwp.contrib.devices.exceptions import DriverError
from .helpers import string2bits, int2hex
from . import conf


DEFAULT_PORT = conf.DEFAULT_PORT
DEFAULT_BOD = conf.DEFAULT_BOD
MIN_TIMEOUT = conf.MIN_TIMEOUT

CR = chr(0x0D)


class DCONError(DriverError):
    pass


class ICPError(DCONError):
    pass


class BaseDCON(object):
    "Базовый класс включает методы непосредственного общения с устройством."
    error = u''

    def __init__(self, port=DEFAULT_PORT, **kwargs):
        """
        Пароли можно передавать в виде набора шестнадцатеричных
        значений, либо в виде обычной ASCII строки. Длина пароля 4
        ASCII символа.

        """
        self.port = port
        self.bod = kwargs.get('bod', DEFAULT_BOD)
        self.parity = kwargs.get('parity', serial.PARITY_NONE)
        self.stopbits = kwargs.get('parity', serial.STOPBITS_ONE)
        self.timeout = kwargs.get('timeout', 0.7)
        self.writeTimeout = kwargs.get('writeTimeout', 0.7)

    @property
    def is_connected(self):
        "Возвращает состояние соединение."
        return bool(self._conn and self.conn.isOpen())

    @property
    def conn(self):
        "Возвращает соединение."
        if hasattr(self, '_conn') and self._conn is not None:
            return self._conn
        self.connect()
        return self._conn

    def check(self):
        "Проверка на готовность."
        if not self.conn.isOpen():
            self.disconnect()
            raise DCONError(_('Serial port closed unexpectedly'))
        return True

    def connect(self):
        "Устанавливает соединение."
        try:
            self._conn = serial.Serial(
                self.port, self.bod,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout,
                writeTimeout=self.writeTimeout
            )
        except Exception as e:
            self._conn = None
            self.error = unicode(e)
            return False

        return self.check()

    def disconnect(self):
        "Закрывает соединение."
        if self.conn:
            self._conn.close()
            self._conn = None
        return True

    def write(self, write):
        "Высокоуровневый метод записи в соединение."
        if not self.conn:
            raise DCONError(self.error)
        return self.conn.write(write)

    def flush(self):
        "Высокоуровневый метод слива в ККТ."
        if not self.conn:
            raise DCONError(self.error)
        return self.conn.flush()

    def read(self):
        "Высокоуровневый метод считывания соединения."
        if not self.conn:
            raise DCONError(self.error)
        result = self.conn.readline()
        return result.strip(CR)

    def send(self, command):
        "Стандартная обработка команды."
        if not self.conn:
            raise DCONError(self.error)

        self.flush()
        self.write(command + CR)
        self.flush()
        return True

    def ask(self, command, sleep=0, disconnect=True):
        """
        Высокоуровневый метод получения ответа. Состоит из последовательной
        цепочки действий.

        Возвращает позиционные параметры: (error, data).

        """
        data = [None, None]
        self.send(command)
        if sleep:
            time.sleep(sleep)
        answer = self.read()
        if disconnect:
            self.disconnect()
        if answer.startswith('?'):
            data[0] = True
        else:
            data[1] = answer.strip('>').strip('!')
        return data


def channels_status(data):
    try:
        data = string2bits(chr(eval('0x' + data[:2])))
    except:
        pass
    else:
        data.reverse()
        data = data
    return data


class ICP(BaseDCON):
    "Класс с командами, исполняемыми согласно протокола DCON."

    def valid_module(self, module):
        "Проверка числа модуля."
        if 0 < int(module) > 255:
            raise ICPError(_('Module must be 0..255'))
        return True

    def valid_channel(self, channel):
        "Проверка числа канала."
        if 0 < int(channel) > 7:
            raise ICPError(_('Channel must be 0..7'))
        return True

    def status(self, module=1):
        "Возвращает статус устройства."
        self.valid_module(module)

        error, data = self.ask('@%s' % int2hex(int(module)))
        if error:
            raise ICPError(self.error.encode('utf-8') or _('Unknown error'))
        else:
            data = channels_status(data)
        return data

    def on(self, module, channel):
        "Команда включения канала на заданном модуле."
        self.valid_module(module)
        self.valid_channel(channel)

        command = '#%s1%d01' % (int2hex(int(module)), int(channel))
        error, data = self.ask(command)
        return False if error else True

    def off(self, module, channel):
        "Команда выключения канала на заданном модуле."
        self.valid_module(module)
        self.valid_channel(channel)

        command = '#%s1%d00' % (int2hex(int(module)), int(channel))
        error, data = self.ask(command)
        return False if error else True


class ICPDummy(object):
    "Класс фиктивного устройства."

    def __init__(self, *args, **kwargs):
        self.modules = [[0, 0, 0, 0, 0, 0, 0, 0] for x in range(255)]

    def valid_module(self, module):
        "Проверка числа модуля."
        if 0 < int(module) > 255:
            raise ICPError(_('Module must be 0..255'))
        return True

    def valid_channel(self, channel):
        "Проверка числа канала."
        if 0 < int(channel) > 7:
            raise ICPError(_('Channel must be 0..7'))
        return True

    def status(self, module=1):
        "Возвращает статус устройства."
        self.valid_module(module)
        return self.modules[module]

    def on(self, module, channel):
        "Команда включения канала на заданном модуле."
        self.valid_module(module)
        self.valid_channel(channel)
        if self.modules[module][channel]:
            return False
        self.modules[module][channel] = 1
        return True

    def off(self, module, channel):
        "Команда выключения канала на заданном модуле."
        self.valid_module(module)
        self.valid_channel(channel)
        if not self.modules[module][channel]:
            return False
        self.modules[module][channel] = 0
        return True
