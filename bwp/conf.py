# -*- coding: utf-8 -*-
#
#  bwp/conf.py
#
#  Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
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
from __future__ import unicode_literals
import os
import datetime

from django import __version__ as DJANGO_VERSION  # NOQA
from django.conf import settings

from quickapi import __version__ as QUICKAPI_VERSION  # NOQA
from bwp import __version__ as BWP_VERSION


BWP_TEMP_UPLOAD_FILE = getattr(
    settings, 'BWP_TEMP_UPLOAD_FILE', 'bwp_tmp_upload'
)
# 3 minutes:
BWP_TEMP_UPLOAD_FILE_EXPIRES = getattr(
    settings, 'BWP_TEMP_UPLOAD_FILE_EXPIRES', 120
)
BWP_TEMP_UPLOAD_FILE_HASH_LENGTH = getattr(
    settings, 'BWP_TEMP_UPLOAD_FILE_HASH_LENGTH', 12
)
BWP_TEMP_UPLOAD_FILE_ANONYMOUS = getattr(
    settings, 'BWP_TEMP_UPLOAD_FILE_ANONYMOUS', False
)

VERSION = getattr(settings, 'VERSION', BWP_VERSION)
VERSION_DATE = getattr(
    settings, 'VERSION_DATE',
    datetime.datetime.fromtimestamp(
        os.stat(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                '__init__.py',
            )
        ).st_mtime
    ).strftime('%d.%m.%Y')
)

PROJECT_NAME = getattr(settings, 'PROJECT_NAME', ('Example project'))
PROJECT_SHORTNAME = getattr(settings, 'PROJECT_SHORTNAME', ('BWP-Example'))
PROJECT_DESCRIPTION = getattr(
    settings, 'PROJECT_DESCRIPTION',
    ('Example project on Business Web Platform')
)

REPORT_FILES_UNIDECODE = getattr(settings, 'REPORT_FILES_UNIDECODE', True)

AUTHORS = getattr(settings, 'AUTHORS', [])
COPYRIGHT = getattr(settings, 'COPYRIGHT', ('Name of company'))
COPYRIGHT_YEAR = getattr(settings, 'COPYRIGHT_YEAR', '2013')
