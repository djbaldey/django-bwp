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
from django.utils.crypto import get_random_string

from bwp.utils.classes import upload_to
from bwp.db import fields

class AbstractOrg(models.Model):
    """ Абстрактная модель организации """
    DOCUMENT_CHOICES = (
        (1,_('certificate')),
        (2,_('license')),
    )
    inn = models.CharField(
            max_length=16,
            default= u'*%s' % get_random_string(16),
            verbose_name = _("INN"))
    title = models.CharField(
            max_length=255,
            verbose_name = _("title"))
    fulltitle = models.TextField(
            blank=True,
            verbose_name = _("full title"))
    kpp = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("KPP"))
    ogrn = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("OGRN"))
    address = models.TextField(
            blank=True,
            verbose_name = _("address"))
    phones = models.TextField(
            blank=True,
            verbose_name = _("phones"))
    
    # Банковские реквизиты
    bank_bik = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("identification code of bank"))
    bank_title = models.TextField(
            blank=True,
            verbose_name = _("title of bank"))
    bank_set_account = models.CharField(
            max_length=32,
            blank=True,
            verbose_name = _("settlement account"))
    bank_cor_account = models.CharField(
            max_length=32,
            blank=True,
            verbose_name = _("correspondent account"))
    # Поля документа клиента
    document_type = models.IntegerField(
            choices=DOCUMENT_CHOICES,
            blank=True, null=True,
            verbose_name = _("type of document"))
    document_series = models.CharField(
            max_length=10,
            blank=True,
            verbose_name = _("series of document"))
    document_number = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("number of document"))
    document_date = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("issue of document"))
    document_org = models.TextField(
            blank=True,
            verbose_name = _("organization of issue"))
    document_code = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("code organization of issue"))

    # прочие поля
    web = models.URLField(
            blank=True,
            verbose_name = _('web site'))
    email = models.EmailField(
            #~ default='no@example.com',
            blank=True,
            verbose_name = _('e-mail address'))
    about = fields.HTMLField(
            blank=True,
            verbose_name = _("about organization"))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']
        abstract = True

class AbstractPerson(models.Model):
    """ Абстрактная модель персоны """
    first_name = models.CharField(
            max_length=30,
            blank=True,
            verbose_name = _('first name'))
    middle_name = models.CharField(
            max_length=30,
            blank=True,
            verbose_name = _('middle name'))
    last_name = models.CharField(
            max_length=30,
            blank=True,
            verbose_name = _('last name'))
    phones = models.CharField(
            max_length=200,
            blank=True,
            verbose_name = _('phones'))
    address = models.TextField(
            blank=True,
            verbose_name = _("address"))
    email = models.EmailField(
            blank=True,
            verbose_name = _('e-mail address'))
    web = models.URLField(
            blank=True,
            verbose_name = _('web site'))
    skype = models.CharField(
            max_length=50,
            blank=True,
            verbose_name = _('skype'))
    jabber = models.EmailField(
            blank=True,
            verbose_name = _('jabber'))
    about = models.TextField(
            blank=True,
            verbose_name = _("about person"))

    def __unicode__(self):
        fio = u' '.join(
                [self.last_name, self.first_name, self.middle_name]
                ).replace("  ", ' ')
        return fio

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name']
        abstract = True

class AbstractGroup(models.Model):
    """ Абстрактная модель группы или категории """
    title = models.CharField(
            max_length=255,
            verbose_name = _('title'))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title',]
        abstract = True

class AbstractGroupUnique(models.Model):
    """ Абстрактная модель уникальной группы или категории """
    title = models.CharField(
            max_length=255,
            unique=True,
            verbose_name = _('title'))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title',]
        abstract = True

class AbstractData(models.Model):
    """ Класс, предоставляющий общие методы для фото, видео-кода, файлов. """
    label = models.CharField(
            max_length=255,
            blank=True,
            verbose_name=_('label'))

    default_label_type = u'%s' % _('file')

    def __unicode__(self):
        return self.label or u'%s' % self.id

    def get_default_label(self):
        c = self.__class__.objects.count() + 1
        return '%s %07d' % (self.default_label_type, c)

    def get_default_filename(self, name=None):
        return u'%s' % unidecode(name).lower().replace(' ', '_')

    def upload_to(self, filename):
        classname = self.__class__.__name__.lower()
        date = datetime.date.today()
        dic = {
            'classname': classname,
            'filename': self.get_default_filename(filename),
            'year': date.year,
            'month': date.month,
            'day': date.day,
        }
        return u'%(classname)s/%(year)s/%(month)s/%(day)s/%(filename)s' % dic

    class Meta:
        abstract = True

class AbstractVideoCode(AbstractData):
    """ Абстрактная модель для видео из внешних источников (код) """
    default_label_type = u'%s' % _('videocode')
    code = models.TextField( 
            verbose_name=_('code'),
            help_text=_("Set your code for video on the www.youtube.com"))

    def save(self):
        self.label = self.label or self.get_default_label()
        super(AbstractVideoCode, self).save()

    class Meta:
        abstract = True

class AbstractImage(AbstractData):
    """ Абстрактная модель для изображений """
    IMGAGE_SETTINGS = {
        'resize': True,
        'thumb_square': True,
        'thumb_width': 256,
        'thumb_height': 256,
        'max_width': 1024,
        'max_height': 1024,
    }
    default_label_type = u'%s' % _('image')
    image = fields.ThumbnailImageField(upload_to=upload_to, 
            verbose_name=_('image'),
            **IMGAGE_SETTINGS)

    def save(self, **kwargs):
        if self.id:
            try:
                presave_obj = self.__class__.objects.get(id=self.id)
            except:
                pass
            else:
                try:
                    presave_obj.image.path
                except:
                    pass
                else:
                    if self.image != presave_obj.image:
                        # delete old image files:
                        for name in (
                            presave_obj.image.path, presave_obj.image.thumb_path, 
                            ):
                            osdelete(name)
        super(AbstractImage, self).save(**kwargs)

    def delete(self, **kwargs):
        # delete files:
        for name in (
            self.image.path, self.image.thumb_path, 
            ):
            osdelete(name)
        super(AbstractImage, self).delete(**kwargs)

    class Meta:
        abstract = True

class AbstractFile(AbstractData):
    """ Абстрактная модель для файлов """
    default_label_type = u'%s' % _('file')
    file = models.FileField(upload_to=upload_to, 
            verbose_name=_('file'))

    def save(self):
        self.label = self.label or self.get_default_label()
        if self.id:
            try:
                presave_obj = self.__class__.objects.get(id=self.id)
            except:
                pass
            else:
                try:
                    presave_obj.file.path
                except:
                    pass
                else:
                    if self.file != presave_obj.file:
                        osdelete(presave_obj.file.path)
        super(AbstractFile, self).save()

    def delete(self):
        osdelete(self.file.path)
        super(AbstractFile, self).delete()

    class Meta:
        abstract = True
