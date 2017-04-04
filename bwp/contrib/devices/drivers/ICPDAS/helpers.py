# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/drivers/ICPDAS/helpers.py
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
from bwp.contrib.devices.drivers.helpers import string2bits  # NOQA
from bwp.contrib.devices.drivers.helpers import bits2string  # NOQA


def get_control_summ(string):
    """ Подсчет CRC """
    result = sum([ord(s) for s in string])
    return chr(result)


def int2hex(integer):
    """ Возвращает очищенный от нуля hex минимальной длинной 2 символа """
    h = hex(integer)[2:].upper()
    if len(h) < 2:
        h = '0' + h
    return h
