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
from bwp.conf import settings

# Путь внутри каталога MEDIA_ROOT
WEBODT_TEMPLATE_PATH = getattr(settings, 'WEBODT_TEMPLATE_PATH', 'webodt')
WEBODT_DEFAULT_FORMAT = getattr(settings, 'WEBODT_DEFAULT_FORMAT', 'doc')
WEBODT_ABIWORD_COMMAND = getattr(settings, 'WEBODT_ABIWORD_COMMAND', ['/usr/bin/abiword', '--plugin', 'AbiCommand'])
WEBODT_GOOGLEDOCS_EMAIL = getattr(settings, 'WEBODT_GOOGLEDOCS_EMAIL', None)
WEBODT_GOOGLEDOCS_PASSWORD = getattr(settings, 'WEBODT_GOOGLEDOCS_PASSWORD', None)
WEBODT_OPENOFFICE_SERVER = getattr(settings, 'WEBODT_OPENOFFICE_SERVER', ('localhost', 2002))
WEBODT_CONVERTER = getattr(settings, 'WEBODT_CONVERTER', 'bwp.contrib.webodt.converters.abiword.AbiwordODFConverter')
WEBODT_TMP_DIR = getattr(settings, 'WEBODT_TMP_DIR', None)
WEBODT_CACHE_DIR = getattr(settings, 'WEBODT_CACHE_DIR', '/tmp/webodt_cache')
WEBODT_ODF_TEMPLATE_PREPROCESSORS = getattr(settings, 'WEBODT_ODF_TEMPLATE_PREPROCESSORS', [
    'bwp.contrib.webodt.preprocessors.xmlfor_preprocessor',
    'bwp.contrib.webodt.preprocessors.unescape_templatetags_preprocessor',
])
