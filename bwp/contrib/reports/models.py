# -*- coding: utf-8 -*-
#
#  bwp/contrib/reports/models.py
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
import os
import hashlib

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bwp import conf
from bwp.conf import settings
from bwp.contrib.abstracts.models import AbstractGroup, AbstractFile
from bwp.contrib.qualifiers.models import Document as GeneralDocument
from bwp.utils import remove_file, remove_dirs


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
        ContentType, verbose_name=_('content type'),
    )
    bound = models.IntegerField(
        _('bound'),
        choices=BOUND_CHOICES,
        default=BOUND_OBJECT,
    )
    template_name = models.CharField(
        _('HTML template name'),
        max_length=255,
    )
    format_out = models.CharField(
        _('format out'),
        max_length=4,
        choices=FORMAT_CHOICES,
        default=FORMAT_CHOICES[0][0],
    )
    qualifier = models.ForeignKey(
        GeneralDocument,
        blank=True, null=True,
        verbose_name=_('qualifier'),
        related_name='reports_document_set',
    )

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
        content = template.render(Context(context)).encode('utf-8')
        return ContentFile(content)

    def render_to_media_url(self, context={}, user=None):
        filename = self.title + '.' + self.format_out
        filename = prep_filename(filename)
        context['DOCUMENT'] = self
        context['user'] = user
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
    created = models.DateTimeField(_('created'), auto_now_add=True)
    document = models.ForeignKey(
        Document,
        editable=False,
        verbose_name=_('document'),
    )
    user = models.ForeignKey(
        User,
        null=True, blank=True,
        editable=False,
        verbose_name=_('user'),
    )

    class Meta:
        ordering = ['-created']
        verbose_name = _('generated report')
        verbose_name_plural = _('generated reports')

    def upload_to(self, filename):
        dt = timezone.now()
        date = dt.date()
        dic = {
            'filename': filename,
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
        return (
            '<a href="%s" target="_blank">'
            'download</a>' % self.file.url.encode('utf-8')
        )

    def delete(self):
        remove_file(self.file.path)
        remove_dirs(os.path.dirname(self.file.path))
        super(Report, self).delete()
