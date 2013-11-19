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
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from bwp.sites import site
from bwp.models import ModelBWP, ComposeBWP, LogEntry,\
        GlobalUserSettings, TempUploadFile, ManyToManyBWP
from bwp import User, Group, Permission, check_builtin_users

class LogEntryAdmin(ModelBWP):
    columns = ('action_time', 'user', '__unicode__', 'id')
    fields_search = (
        'user__username__icontains',
        'object_repr__icontains',
        'change_message__icontains'
    )
    allow_clone = False
site.register_model(LogEntry, LogEntryAdmin)

site.register_model(GlobalUserSettings)

class TempUploadFileAdmin(ModelBWP):
    columns = ('__unicode__', 'user', 'created')
site.register_model(TempUploadFile, TempUploadFileAdmin)

if not check_builtin_users():
    class PermissionAdmin(ModelBWP):
        fields_search = (
            'name__icontains',
            'codename__icontains',
            'content_type__name__icontains',
            'content_type__app_label__icontains',
            'content_type__model__icontains',
        )
    site.register_model(Permission, PermissionAdmin)

    class PermissionCompose(ManyToManyBWP):
        columns = ('__unicode__', 'name', 'codename', 'id')
        fields_search = (
            'name__icontains',
            'codename__icontains',
            'content_type__name__icontains',
            'content_type__app_label__icontains',
            'content_type__model__icontains',
        )
        model = Permission

    class UserAdmin(ModelBWP):
        columns = ('__unicode__',
            'is_active',
            'is_superuser',
            'is_staff',
            'last_login',
            'date_joined',
            'id')
        ordering = ('username',)
        fields_exclude = ['password',]
        fields_search = ('username', 'email')
        compositions = [
            ('user_permissions', PermissionCompose),
        ]
    site.register_model(User, UserAdmin)

    class UserCompose(ComposeBWP):
        model = User
        columns = ('__unicode__',
            'is_active',
            'is_superuser',
            'is_staff',
            'last_login',
            'date_joined',
            'id')
        ordering = ('username',)

    class GroupAdmin(ModelBWP):
        compositions = [
            ('user_set', UserCompose),
            #~ ('permissions', PermissionCompose),
        ]
    site.register_model(Group, GroupAdmin)

    class ContentTypeAdmin(ModelBWP):
        columns = ('name', 'app_label', 'model', 'id')
        ordering = ('app_label', 'model')
    site.register_model(ContentType, ContentTypeAdmin)
