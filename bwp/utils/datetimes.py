# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
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
import datetime

def dt_rounded(dt=None, minute=True, hour=False, day=False):
    """ Округление времени до секунды, минуты, часа или дня.
        По умолчанию до минуты.

        до дня:     rounded(day=True)
        до часа:    rounded(hour=True)
        до минуты:  rounded()
        до секунды: rounded(minute=False)
        
        Если нужно округлить заданное время,то оно передаётся в
        параметре `dt`
    """
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.now()

    if day:
        dt = datetime.datetime(dt.year, dt.month, dt.day)
    elif hour:
        dt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour)
    elif minute:
        dt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute)
    else:
        dt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    return dt
