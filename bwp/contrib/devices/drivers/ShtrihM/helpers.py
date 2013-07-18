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
from bwp.contrib.devices.drivers.helpers import int2, int4, int5, int6,\
    string2bits, bits2string

def money2integer(money, digits=2):
    """ Преобразует decimal или float значения в целое число, согласно
        установленной десятичной кратности.
        
        Например, money2integer(2.3456, digits=3) вернёт  2346
    """
    return int(round(round(float(money), digits) * 10**digits))

def integer2money(integer, digits=2):
    """ Преобразует целое число в значение float, согласно
        установленной десятичной кратности.
        
        Например, integer2money(2346, digits=3) вернёт  2.346
    """
    return round(float(integer) / 10**digits, digits)

def count2integer(count, coefficient=1, digits=3):
    """ Преобразует количество согласно заданного коэффициента """
    return money2integer(count, digits=digits) * coefficient

def get_control_summ(string):
    """ Подсчет CRC """
    result = 0
    for s in string:
        result = result ^ ord(s)
    return chr(result)

def digits2string(digits):
    """ Преобразует список из целых или шестнадцатеричных значений в
        строку
    """
    return ''.join([ chr(x) for x in digits ])

