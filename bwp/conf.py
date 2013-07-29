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
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
import bwp, os, datetime, quickapi

QUICKAPI_VERSION        = quickapi.__version__

BWP_VERSION             = bwp.__version__

BWP_TEMP_UPLOAD_FILE          = getattr(settings, 'BWP_TEMP_UPLOAD_FILE', 'bwp_tmp_upload')
BWP_TEMP_UPLOAD_FILE_EXPIRES  = getattr(settings, 'BWP_TEMP_UPLOAD_FILE_EXPIRES', 120) # 3 minutes
BWP_TEMP_UPLOAD_FILE_HASH_LENGTH = getattr(settings, 'BWP_TEMP_UPLOAD_FILE_HASH_LENGTH', 12)
BWP_TEMP_UPLOAD_FILE_ANONYMOUS   = getattr(settings, 'BWP_TEMP_UPLOAD_FILE_ANONYMOUS', False)

VERSION                 = getattr(settings, 'VERSION',         BWP_VERSION)
VERSION_DATE            = getattr(settings, 'VERSION_DATE',
    datetime.datetime.fromtimestamp(
        os.stat(os.path.join(os.path.abspath(os.path.dirname(__file__)), '__init__.py')).st_mtime
    ).strftime("%d.%m.%Yг.")
)

PROJECT_NAME            = getattr(settings, 'PROJECT_NAME',             _(u'Example project'))
PROJECT_SHORTNAME       = getattr(settings, 'PROJECT_SHORTNAME',        _(u'BWP-Example'))
PROJECT_DESCRIPTION     = getattr(settings, 'PROJECT_DESCRIPTION',      _(u'Example project on Business Web Platform'))

DJANGO_VERSION          = getattr(settings, 'DJANGO_VERSION',           '1.4')
BOOTSTRAP_VERSION       = getattr(settings, 'BOOTSTRAP_VERSION',        '2.3.1')
JQUERY_VERSION          = getattr(settings, 'JQUERY_VERSION',           '1.9.1')
JQUERY_JSON_VERSION     = getattr(settings, 'JQUERY_JSON_VERSION',      '2.4')
UNDERSCORE_VERSION      = getattr(settings, 'UNDERSCORE_VERSION',       '1.4.4')
UNDERSCORE_STRING_VERSION = getattr(settings, 'UNDERSCORE_STRING_VERSION', '2.3.0')

REPORT_FILES_UNIDECODE = getattr(settings, 'REPORT_FILES_UNIDECODE', True)

AUTHORS                 = getattr(settings, 'AUTHORS',                  [])
COPYRIGHT               = getattr(settings, 'COPYRIGHT',                _(u'Name of company'))
COPYRIGHT_YEAR          = getattr(settings, 'COPYRIGHT_YEAR',           '2013')
