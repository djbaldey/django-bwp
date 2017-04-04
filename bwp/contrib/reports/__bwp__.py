# -*- coding: utf-8 -*-
#
#  bwp/contrib/reports/__bwp__.py
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
from bwp.sites import site
from bwp.models import ModelBWP
from models import Document, Report


class DocumentBWP(ModelBWP):
    list_display = (
        'title',
        'content_type',
        'qualifier',
        'template_name',
        'id',
    )
    ordering = ['content_type']


site.register(Document, DocumentBWP)


class ReportBWP(ModelBWP):
    list_display = ('document', 'created', 'user', 'url', 'id')
    search_fields = ['document__title']


site.register(Report, ReportBWP)
