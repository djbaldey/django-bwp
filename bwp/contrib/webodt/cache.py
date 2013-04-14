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
import os
import hashlib
from bwp.contrib.webodt.conf import WEBODT_CACHE_DIR, settings
from bwp.contrib.webodt import Document

class CacheManager(object):

    def __init__(self):
        if not os.path.isdir(WEBODT_CACHE_DIR):
            os.makedirs(WEBODT_CACHE_DIR)

    def get(self, odf_document, format):
        filename = self.get_filename(odf_document, format)
        if os.path.isfile(filename):
            return Document(filename, delete_on_close=False)
        return None

    def set(self, odf_document, format, document):
        filename = self.get_filename(odf_document, format)
        fd = open(filename, 'w')
        document.seek(0)
        fd.write(document.read())
        document.seek(0)
        fd.close()

    def delete(self, odf_document, format):
        filename = self.get_filename(odf_document, format)
        if os.path.isfile(filename):
            os.unlink(filename)

    def get_filename(self, odf_document, format):
        sha1 = hashlib.new('sha1')
        odf_document.seek(0)
        odf_data = odf_document.read()
        sha1.update(odf_data)
        odf_document.seek(0)
        sha1.update(format)
        sha1.update(settings.SECRET_KEY)
        digest = sha1.hexdigest()
        filename = os.path.join(WEBODT_CACHE_DIR, '%s.%s' % (digest, format))
        return filename

    def clear(self):
        for filename in os.listdir(WEBODT_CACHE_DIR):
            path = os.path.join(WEBODT_CACHE_DIR, filename)
            if os.path.isfile(path):
                os.unlink(path)
