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
from django.contrib.auth.models import User
from django.template import Context
from django.template.loader import get_template
from django.core.files.base import ContentFile

from bwp.contrib.abstracts.models import AbstractGroup, AbstractFile
from bwp.contrib.qualifiers.models import Document as GeneralDocument
from bwp import conf
from bwp.conf import settings
from bwp.utils import remove_file, remove_dirs

import os, datetime, hashlib

if conf.REPORT_FILES_UNIDECODE:
    from unidecode import unidecode
    prep_filename = lambda x: unidecode(x).replace(' ', '_').replace("'", "")
else:
    prep_filename = lambda x: x

class Document(AbstractGroup):
    """ Документ.

        Шаблоном документа может выступать html или txt файлы.
        В форматы ODS и ODT не конвертируется, а всего лишь заменяет
        расширение файла для автоматического открытия в ApacheOffice или
        LibreOffice. Поэтому основу таких шаблонов стоит готовить в
        нужном приложении и сохранять как HTML.
    """
    BOUND_OBJECT = 1
    BOUND_MODEL = 2
    BOUND_CHOICES = (
        (BOUND_OBJECT, _('object')),
        (BOUND_MODEL, _('model')),
    )

    FORMAT_CHOICES = (
        ('html', _('HTML page')),
        ('txt', _('plain text')),
        ('odt', _('text document (ODT)')),
        ('ods', _('spreadsheet (ODS)')),
    )

    content_type = models.ForeignKey(
            ContentType,
            verbose_name = _('content type'))
    bound = models.IntegerField(
            choices=BOUND_CHOICES,
            default=BOUND_OBJECT,
            verbose_name = _('bound'))
    template_name = models.CharField(
            max_length=255,
            verbose_name = _('HTML template name'))
    format_out = models.CharField(
            max_length=4,
            choices=FORMAT_CHOICES,
            default=FORMAT_CHOICES[0][0],
            verbose_name = _('format out'))
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

    def render(self, context):
        """ Return rendered instance of ContentFile """
        template = get_template(self.template_name)
        content  = template.render(Context(context)).encode('utf-8')
        return ContentFile(content)

    def render_to_media_url(self, context={}, user=None):
        filename = self.title+'.'+self.format_out
        filename = prep_filename(filename)
        context['DOCUMENT'] = self
        _file = self.render(context)
        report = Report(
            document=self,
            label=filename,
            user=user,
        )
        report.file.save(filename, _file, save=False)
        report.save()
        return report.file.url

    @property
    def for_object(self):
        return bool(self.bound == Document.BOUND_OBJECT)

    @property
    def for_model(self):
        return bool(self.bound == Document.BOUND_MODEL)

class Report(AbstractFile):
    """ Файл сформированного документа """
    default_label_type = u'%s' % _('report')
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('created'))
    document = models.ForeignKey(
            Document,
            editable=False,
            verbose_name = _('document'))
    user = models.ForeignKey(
            User,
            null=True, blank=True,
            editable=False,
            verbose_name = _('user'))

    class Meta:
        ordering = ['-created']
        verbose_name = _('generated report')
        verbose_name_plural = _('generated reports')

    def upload_to(self, filename):
        dt = datetime.datetime.now()
        date = dt.date()
        dic = {
            'filename':filename,
            'date': date.isoformat(),
        }
        sha1 = hashlib.new('md5')
        sha1.update(str(dt.isoformat()))
        sha1.update(settings.SECRET_KEY)
        digest = sha1.hexdigest()
        dic['digest'] = digest
        return u'reports/%(date)s/%(digest)s/%(filename)s' % dic

    @property
    def url(self):
        return '<a href="%s" target="_blank">download</a>' % (self.file.url.encode('utf-8'),)

    def delete(self):
        remove_file(self.file.path)
        remove_dirs(os.path.dirname(self.file.path))
        super(Report, self).delete()


