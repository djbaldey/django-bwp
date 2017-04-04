# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/drivers/helpers.py
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
import struct


class Struct(struct.Struct):
    """ Преобразователь """
    def __init__(self, *args, **kwargs):
        self.length = kwargs.pop('length', None)
        super(Struct, self).__init__(*args, **kwargs)

    def unpack(self, value):
        value = self.pre_value(value)
        return super(Struct, self).unpack(value)[0]

    def pack(self, value):
        value = super(Struct, self).pack(value)
        return self.post_value(value)

    def pre_value(self, value):
        """ Обрезает или добавляет нулевые байты """
        if self.size:
            if self.format in ('h', 'i', 'I', 'l', 'L', 'q', 'Q'):
                _len = len(value)
                if _len < self.size:
                    value = value.ljust(self.size, chr(0x0))
                elif _len > self.size:
                    value = value[:self.size]
        return value

    def post_value(self, value):
        """ Обрезает или добавляет нулевые байты """
        if self.length:
            if self.format in ('h', 'i', 'I', 'l', 'L', 'q', 'Q'):
                _len = len(value)
                if _len < self.length:
                    value = value.ljust(self.length, chr(0x0))
                elif _len > self.length:
                    value = value[:self.length]
        return value


# Объекты класса Struct
# Формат short по длинне 2 байта
int2 = Struct('h', length=2)
# Формат int по длинне 3 байта
int3 = Struct('i', length=3)
# Формат int == long по длинне 4 байта
int4 = Struct('i', length=4)
# Формат "long long" для 5-ти байтовых чисел
int5 = Struct('q', length=5)
# Формат "long long" для 6-ти байтовых чисел
int6 = Struct('q', length=6)
# Формат "long long" для 7-ти байтовых чисел
int7 = Struct('q', length=7)
# Формат "long long" для 8-ти байтовых чисел
int8 = Struct('q', length=8)


def string2bits(string):
    """ Convert string to bit array """
    result = []
    for char in string:
        bits = bin(ord(char))[2:]
        bits = '00000000'[len(bits):] + bits
        result.extend([int(b) for b in bits])
    return result


def bits2string(bits):
    """ Convert bit array to string """
    chars = []
    for b in range(len(bits) / 8):
        start = b * 8
        end = (b + 1) * 8
        byte = bits[start:end]
        chars.append(chr(int(''.join([str(bit) for bit in byte]), 2)))
    return ''.join(chars)
