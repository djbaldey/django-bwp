# -*- coding: utf-8 -*-
#
#  bwp/utils/classes.py
#
#  Copyright 2012 Grigoriy Kramarenko <root@rosix.ru>
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


def upload_to(cls, filename):
    """ Именованная функция-ссылка на метод ещё неопределённого класса """
    return cls.upload_to(filename)


def autonumber(cls, field):
    """ Именованная функция-ссылка на метод ещё неопределённого класса """
    return cls.autonumber(field)
