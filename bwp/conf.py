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
import bwp

BWP_VERSION             = bwp.__version__

PROJECT_NAME            = getattr(settings, 'PROJECT_NAME',             'PROJECT_NAME')
PROJECT_SHORTNAME       = getattr(settings, 'PROJECT_SHORTNAME',        'PROJECT_SHORTNAME')
PROJECT_DESCRIPTION     = getattr(settings, 'PROJECT_DESCRIPTION',      'PROJECT_DESCRIPTION')

VERSION                 = getattr(settings, 'VERSION',                  '1.0')
VERSION_DATE            = getattr(settings, 'VERSION_DATE',             '')

DJANGO_VERSION          = getattr(settings, 'DJANGO_VERSION',           '1.4')
BOOTSTRAP_VERSION       = getattr(settings, 'BOOTSTRAP_VERSION',        '2.3.1')
JQUERY_VERSION          = getattr(settings, 'JQUERY_VERSION',           '1.9.1')
JQUERY_JSON_VERSION     = getattr(settings, 'JQUERY_JSON_VERSION',      '2.4')
DATATABLES_VERSION      = getattr(settings, 'DATATABLES_VERSION',       '1.9.4')
JS_JINJA_VERSION        = getattr(settings, 'JS_JINJA_VERSION',         '1.0')

AUTHORS                 = getattr(settings, 'AUTHORS',                  [])
COPYRIGHT               = getattr(settings, 'COPYRIGHT',                'Company Name')
COPYRIGHT_YEAR          = getattr(settings, 'COPYRIGHT_YEAR',           '2013')

ARRAY_FORM_OBJECT_KEY   = getattr(settings, 'ARRAY_FORM_OBJECT_KEY',    'ARRAY_FORM_OBJECT_KEY')
ARRAY_FORM_COMPOSE_KEY  = getattr(settings, 'ARRAY_FORM_COMPOSE_KEY',   'ARRAY_FORM_COMPOSE_KEY')

