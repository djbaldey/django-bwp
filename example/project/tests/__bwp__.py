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
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from bwp.sites import site
from bwp.models import ModelBWP, ComposeBWP
from models import *

class OrgCompose(ComposeBWP):
    list_display = ('__unicode__', ('get_group', _('group')), 'pk', 'id')
    #~ fields = ('title', 'fulltitle')
    model = Org

class PersonCompose(ComposeBWP):
    model = Person

class VideoCodeCompose(ComposeBWP):
    model = VideoCode

class ImageCompose(ComposeBWP):
    model = Image

class FileCompose(ComposeBWP):
    model = File

class GroupAdmin(ModelBWP):
    compositions = [
        ('org_set',         OrgCompose),
        ('person_set',      PersonCompose),
        ('videocode_set',   VideoCodeCompose),
        ('image_set',       ImageCompose),
        ('file_set',        FileCompose),
    ]
site.register(Group, GroupAdmin)
admin.site.register(Group, admin.ModelAdmin)

class GroupUniqueAdmin(ModelBWP):
    compositions = [
        ('org_set',         OrgCompose),
        ('person_set',      PersonCompose),
        ('videocode_set',   VideoCodeCompose),
        ('image_set',       ImageCompose),
        ('file_set',        FileCompose),
    ]
site.register(GroupUnique, GroupUniqueAdmin)
admin.site.register(GroupUnique, admin.ModelAdmin)

class OrgAdmin(ModelBWP):
    list_display = ('__unicode__', ('get_group', _('group')), 'pk', 'id')
    pass
site.register(Org, OrgAdmin)
admin.site.register(Org, admin.ModelAdmin)

class PersonAdmin(ModelBWP):
    pass
site.register(Person, PersonAdmin)
admin.site.register(Person, admin.ModelAdmin)

class VideoCodeAdmin(ModelBWP):
    pass
site.register(VideoCode, VideoCodeAdmin)
admin.site.register(VideoCode, admin.ModelAdmin)

class ImageAdmin(ModelBWP):
    pass
site.register(Image, ImageAdmin)
admin.site.register(Image, admin.ModelAdmin)

class FileAdmin(ModelBWP):
    pass
site.register(File, FileAdmin)
admin.site.register(File, admin.ModelAdmin)
