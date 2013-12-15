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
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from bwp.sites import site
from bwp.contrib.users.models import User, Group, Permission
from bwp.models import ModelBWP, ComponentBWP

label_id = _('ID')
label_pk = _('PK')

class PermissionBWP(ModelBWP):
    fields_search = (
        'name__icontains',
        'codename__icontains',
        'content_type__name__icontains',
        'content_type__app_label__icontains',
        'content_type__model__icontains',
    )
site.register_model(Permission, PermissionBWP)

class UserBWP(ModelBWP):
    columns = ('__unicode__',
        'is_active',
        'is_superuser',
        'is_staff',
        'last_login',
        'created',
        'id')
    ordering = ('username',)
    fields_exclude = ['password',]
    fields_search = ('username', 'email')
site.register_model(User, UserBWP)

class GroupBWP(ModelBWP):
    components = (
        ComponentBWP(
            site=site, model=User, field='groups',
            ordering = ('username',),
            columns = ('__unicode__',
                'is_active',
                'is_superuser',
                'is_staff',
                'last_login',
                'created',
                'id'
            ),
        ),
    )
site.register_model(Group, GroupBWP)

class ContentTypeBWP(ModelBWP):
    columns = ('name', 'app_label', 'model', 'id')
    ordering = ('app_label', 'model')
site.register_model(ContentType, ContentTypeBWP)
