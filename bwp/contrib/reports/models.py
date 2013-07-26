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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.template import Context

from bwp.contrib.abstracts.models import AbstractGroup
from bwp.contrib.qualifiers.models import Document as GeneralDocument
from bwp.contrib import webodt
from bwp.contrib.webodt.shortcuts import render_to_response
from bwp.contrib.webodt import conf as webodt_conf
from bwp.conf import settings
from bwp.utils import remove_file

import os

class Document(AbstractGroup):
    """ Документ """
    BOUND_OBJECT = 1
    BOUND_MODEL = 2
    BOUND_CHOICES = (
        (BOUND_OBJECT, _('object')),
        (BOUND_MODEL, _('model')),
    )

    content_type = models.ForeignKey(
            ContentType,
            verbose_name = _('content type'))
    bound = models.IntegerField(
            choices=BOUND_CHOICES,
            default=BOUND_OBJECT,
            verbose_name = _('bound'))
    webodt = models.FileField(upload_to=webodt_conf.WEBODT_TEMPLATE_PATH,
            verbose_name = _('template file'))
    qualifier = models.ForeignKey(
            GeneralDocument,
            blank=True, null=True,
            related_name='reports_document_set',
            verbose_name = _('qualifier'))

    class Meta:
        ordering = ['qualifier', 'title']
        verbose_name = _('document')
        verbose_name_plural = _('documents')

    def __unicode__(self):
        if self.qualifier:
            return unicode(self.qualifier)
        return self.title

    def render_to_response(self, dictionary=None, filename=None, format='odt'):
        filename = filename or unicode(self.document).encode('utf-8')
        temlate_name = os.path.basename(self.webodt.name)
        return render_to_response(temlate_name,
            format=format, dictionary=dictionary, filename=filename)

    @property
    def for_object(self):
        return bool(self.bound == Document.BOUND_OBJECT)

    @property
    def for_model(self):
        return bool(self.bound == Document.BOUND_MODEL)

    def save(self, **kwargs):
        if self.id:
            old = self._default_manager.get(id=self.id)
            try:
                old.webodt.path
            except:
                pass
            else:
                if self.webodt != old.webodt:
                    remove_file(old.webodt.path)
        super(Document, self).save(**kwargs)

    def delete(self, **kwargs):
        try:
            self.webodt.path
        except:
            pass
        else:
            remove_file(self.webodt.path)
        super(Document, self).delete(**kwargs)



