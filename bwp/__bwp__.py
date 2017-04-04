# -*- coding: utf-8 -*-
#
#  bwp/__bwp__.py
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
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from bwp.sites import site
from bwp.models import (ModelBWP, ComposeBWP, LogEntry,
                        GlobalUserSettings, TempUploadFile, ManyToManyBWP)


label_id = _('ID')
label_pk = _('PK')


class PermissionAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    search_fields = (
        'name',
        'codename',
        'content_type__app_label',
        'content_type__model',
    )
site.register(Permission, PermissionAdmin)


class PermissionCompose(ManyToManyBWP):
    list_display = ('__unicode__', 'name', 'codename', 'id')
    search_fields = (
        'name',
        'codename',
        'content_type__app_label',
        'content_type__model',
    )
    model = Permission


class UserAdmin(ModelBWP):
    list_display = (
        '__unicode__',
        'is_active',
        'is_superuser',
        'is_staff',
        'last_login',
        'date_joined',
        'id',
    )
    list_display_css = {
        'pk': 'input-micro',
        'id': 'input-micro',
        'is_superuser': 'input-mini',
        'is_staff': 'input-mini',
    }
    ordering = ('username',)
    exclude = ['password']
    search_fields = ('username', 'email')
    compositions = [
        ('user_permissions', PermissionCompose),
    ]
site.register(User, UserAdmin)


class UserCompose(ComposeBWP):
    model = User
    list_display = (
        '__unicode__',
        'is_active',
        'is_superuser',
        'is_staff',
        'last_login',
        'date_joined',
        'id',
    )
    list_display_css = {
        'pk': 'input-micro',
        'id': 'input-micro',
        'is_superuser': 'input-mini',
        'is_staff': 'input-mini',
    }
    ordering = ('username',)


class GroupAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
    compositions = [
        ('user_set', UserCompose),
        ('permissions', PermissionCompose),
    ]
site.register(Group, GroupAdmin)


class ContentTypeAdmin(ModelBWP):
    list_display = ('name', 'app_label', 'model', 'id')
    ordering = ('app_label', 'model')
    hidden = True
site.register(ContentType, ContentTypeAdmin)


class LogEntryAdmin(ModelBWP):
    list_display = ('action_time', 'user', '__unicode__', 'id')
    search_fields = ('user__username', 'object_repr', 'change_message')
    allow_clone = False
site.register(LogEntry, LogEntryAdmin)


class GlobalUserSettingsAdmin(ModelBWP):
    list_display = ('__unicode__', 'id')
site.register(GlobalUserSettings, GlobalUserSettingsAdmin)


class TempUploadFileAdmin(ModelBWP):
    list_display = ('__unicode__', 'user', 'created')
site.register(TempUploadFile, TempUploadFileAdmin)
