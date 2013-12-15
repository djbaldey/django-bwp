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
from bwp.sites import site
from bwp.models import ModelBWP, ComponentBWP
from models import *

class OrgComponent(ComponentBWP):
    columns = ('__unicode__', ('get_group', _('group')), 'pk', 'id')
    site = site
    model = Org

class PersonComponent(ComponentBWP):
    site = site
    model = Person

class VideoCodeComponent(ComponentBWP):
    site = site
    model = VideoCode

class ImageComponent(ComponentBWP):
    site = site
    model = Image

class FileComponent(ComponentBWP):
    site = site
    model = File

class GroupBWP(ModelBWP):
    components = [
        OrgComponent(field='group'),
        PersonComponent(field='group'),
        VideoCodeComponent(field='group'),
        ImageComponent(field='group'),
        FileComponent(field='group'),
    ]
site.register(Group, GroupBWP)

class GroupUniqueBWP(ModelBWP):
    components = [
        OrgComponent(field='groupunique'),
        PersonComponent(field='groupunique'),
        VideoCodeComponent(field='groupunique'),
        ImageComponent(field='groupunique'),
        FileComponent(field='groupunique'),
    ]
site.register(GroupUnique, GroupUniqueBWP)

class OrgBWP(ModelBWP):
    columns = ('__unicode__', ('get_group', _('group')), 'pk', 'id')
    pass
site.register(Org, OrgBWP)

class PersonBWP(ModelBWP):
    pass
site.register(Person, PersonBWP)

class VideoCodeBWP(ModelBWP):
    pass
site.register(VideoCode, VideoCodeBWP)

class ImageBWP(ModelBWP):
    pass
site.register(Image, ImageBWP)

class FileBWP(ModelBWP):
    pass
site.register(File, FileBWP)
