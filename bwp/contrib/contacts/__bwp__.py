# -*- coding: utf-8 -*-
#
#  bwp/contrib/contacts/__bwp__.py
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
from models import Person, Org


class PersonAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    search_fields = ['last_name', 'first_name', 'middle_name', 'id']
    raw_id_fields = ['user']
site.register(Person, PersonAdmin)


class OrgAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
site.register(Org, OrgAdmin)
