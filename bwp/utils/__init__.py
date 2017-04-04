# -*- coding: utf-8 -*-
#
#  bwp/utils/__init__.py
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
from django.conf import settings
import os


def remove_dirs(dirname):
    """ Замалчивание ошибки удаления каталога """
    try:
        os.removedirs(dirname)
        return True
    except:
        return False


def remove_file(filename):
    """ Замалчивание ошибки удаления файла """
    try:
        os.remove(filename)
        return True
    except:
        return False


# Deprecated
osdelete = remove_file


def print_debug(*args):
    if settings.DEBUG:
        for arg in args:
            print(arg)


def print_f_code(f_code):
    print('line %s:\t%s\t%s' % (
        f_code.co_firstlineno,
        os.path.basename(f_code.co_filename),
        f_code.co_name,
    ))


def get_slug_datetime_iso(datetime_value, as_list=False, as_os_path=False):
    iso = datetime_value.isoformat().replace(
        'T', '-T-'
    ).replace(':', '-').replace('.', '-')
    if as_os_path:
        return os.path.join(iso.split('-'))
    if as_list:
        return iso.split('-')
    return iso


def make_list(val):
    if val and not isinstance(val, (list, tuple)):
        return [val]
    return val
