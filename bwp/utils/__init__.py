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
        #~ print '<DEBUG START>'
        for arg in args:
            print arg,
        print '\n'#'\n<DEBUG END>\n'

def print_f_code(f_code):
    print 'line %s:\t%s\t%s' % (
            f_code.co_firstlineno,
            os.path.basename(f_code.co_filename),
            f_code.co_name,
        )

def get_slug_datetime_iso(datetime_value, as_list=False, as_os_path=False):
    iso = datetime_value.isoformat().replace(
        'T', '-T-').replace(':','-').replace('.','-')
    if as_os_path:
        return os.path.join(iso.split('-'))
    if as_list:
        return iso.split('-')
    return iso


