# -*- coding: utf-8 -*-
#
#  bwp/contrib/contacts/models.py
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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from bwp.contrib.abstracts.models import AbstractOrg, AbstractPerson
from bwp.db import managers, fields
from bwp.utils.classes import upload_to


class Person(AbstractPerson):
    """ Персоналии """
    IMAGE_SETTINGS = {
        'resize': True,
        'thumb_square': True,
        'thumb_width': 256,
        'thumb_height': 256,
        'max_width': 1024,
        'max_height': 1024,
    }
    user = models.ForeignKey(User, null=True, blank=True,
                             verbose_name=_('user'))
    photo = fields.ThumbnailImageField(
        upload_to=upload_to,
        null=True, blank=True,
        verbose_name=_('photo'),
        **IMAGE_SETTINGS
    )

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name']
        verbose_name = _('person')
        verbose_name_plural = _('persons')

    @property
    def image(self):
        return self.photo.image


class Org(AbstractOrg):
    """ Организации """
    is_supplier = models.BooleanField(_("is supplier"), default=False)
    is_active = models.BooleanField(_("is active"), default=True)

    admin_objects = models.Manager()
    objects = managers.ActiveManager()

    class Meta:
        verbose_name = _("org")
        verbose_name_plural = _("orgs")
        unique_together = ('inn',)
