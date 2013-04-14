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
import tempfile
from django.utils.importlib import import_module
from bwp.contrib.webodt.conf import WEBODT_DEFAULT_FORMAT, WEBODT_CONVERTER, WEBODT_TMP_DIR

def converter():
    """ Create and return Converter instance
    on a basis of ``WEBODT_CONVERTER`` settings variable
    """
    try:
        module_name, class_name = WEBODT_CONVERTER.rsplit('.', 1)
    except ValueError: # need more than 1 value to unpack
        raise ValueError(
            'WEBODT_CONVERTER %s have to be written in the form of "package.name.ClassName"' % WEBODT_CONVERTER)
    mod = import_module(module_name)
    Converter = getattr(mod, class_name)
    return Converter()


class ODFConverter(object):
    """ Base class for all built-in converter backends """

    WEBODT_DEFAULT_FORMAT = 'doc'

    def convert(self, document, format=None, output_filename=None, delete_on_close=True):
        """ convert document and return file-like object representing output
        document """
        raise NotImplementedError("Should be implemented in subclass")

    def _guess_format_and_filename(self, filename, format):
        """ guess format and filename of the output document

        Either format and filename or both can be undefined (None) variables.
        Function determines undefined variables on basis of file extension or
        default values. If needed, temporary file will be created and returned.

        @return: tuple of strings (filename, format)
        """
        # filename is defined, format is undefined
        if filename and '.' in filename and not format:
            format = filename.split('.')[-1]
        # format is undefined
        if not format:
            format = WEBODT_DEFAULT_FORMAT
        # filename is undefined
        if not filename:
            _, filename = tempfile.mkstemp(suffix = '.' + format, dir=WEBODT_TMP_DIR)
        return filename, format
