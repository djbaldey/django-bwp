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
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django.utils import dateformat
from django.contrib.auth.models import User
from django.conf import settings 

from bwp.utils.classes import upload_to
from bwp.utils.filters import filterQueryset
from bwp.utils import remove_file
from bwp.db import fields
import datetime, os
from unidecode import unidecode

class AbstractOrg(models.Model):
    """ Абстрактная модель организации """
    DOCUMENT_CHOICES = (
        (1,_('certificate')),
        (2,_('license')),
    )
    inn = models.CharField(
            max_length=16,
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
            verbose_name = _("BIK"),
            help_text = _("identification code of bank"))
    bank_title = models.TextField(
            blank=True,
            verbose_name = _("title"),
            help_text = _("title of bank"))
    bank_set_account = models.CharField(
            max_length=32,
            blank=True,
            verbose_name = _("set/account"),
            help_text = _("settlement account"))
    bank_cor_account = models.CharField(
            max_length=32,
            blank=True,
            verbose_name = _("cor/account"),
            help_text = _("correspondent account"))
    # Поля документа клиента
    document_type = models.IntegerField(
            choices=DOCUMENT_CHOICES,
            blank=True, null=True,
            verbose_name = _("type"),
            help_text = _("type of document"))
    document_series = models.CharField(
            max_length=10,
            blank=True,
            verbose_name = _("series"),
            help_text = _("series of document"))
    document_number = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("number"),
            help_text = _("number of document"))
    document_date = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("issue"),
            help_text = _("issue of document"))
    document_org = models.TextField(
            blank=True,
            verbose_name = _("organ"),
            help_text = _("organization of issue"))
    document_code = models.CharField(
            max_length=16,
            blank=True,
            verbose_name = _("code organ"),
            help_text = _("code organization of issue"))

    # прочие поля
    web = models.URLField(
            blank=True,
            verbose_name = _('site'),
            help_text = _('web site'))
    email = models.EmailField(
            #~ default='no@example.com',
            blank=True,
            verbose_name = _('email'),
            help_text = _('email address'))
    about = fields.HTMLField(
            blank=True,
            verbose_name = _("about"),
            help_text = _("about organization"))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']
        abstract = True

class AbstractPerson(models.Model):
    """ Абстрактная модель персоны """
    last_name = models.CharField(
            max_length=30,
            verbose_name = _('last name'))
    first_name = models.CharField(
            max_length=30,
            blank=True,
            verbose_name = _('first name'))
    middle_name = models.CharField(
            max_length=30,
            blank=True,
            verbose_name = _('middle name'))
    phones = models.CharField(
            max_length=200,
            blank=True,
            verbose_name = _('phones'))
    address = models.TextField(
            blank=True,
            verbose_name = _("address"))
    email = models.EmailField(
            blank=True,
            verbose_name = _('email'),
            help_text = _('email address'))
    web = models.URLField(
            blank=True,
            verbose_name = _('site'),
            help_text = _('web site'))
    skype = models.CharField(
            max_length=50,
            blank=True,
            verbose_name = _('skype'))
    jabber = models.EmailField(
            blank=True,
            verbose_name = _('jabber'))
    about = models.TextField(
            blank=True,
            verbose_name = _("about"),
            help_text = _("about person"))

    def __unicode__(self):
        fio = u' '.join(
                [self.last_name, self.first_name, self.middle_name]
                ).replace("  ", ' ')
        return fio

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name']
        abstract = True
    
    def get_short_name(self):
        first = self.first_name[0] if self.first_name else None
        middle = self.middle_name[0] if self.middle_name else None
        res = None
        if first and middle:
            res = u'%s %s.%s.' % (self.last_name, first, middle)
        elif first:
            res = u'%s %s.' % (self.last_name, first)
        return res or u'%s' % (self.last_name,)

class AbstractDocumentDate(models.Model):
    """ Абстрактная модель датированных документов """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    date = models.DateField(
            null=True, blank=True,
            verbose_name = _("date"))

    def __unicode__(self):
        if self.pk:
            doc = self._meta.verbose_name.split(' ')
            doc[0] = doc[0].title()
            return _('%(document)s from %(date)s') % {
                'document': ' '.join(doc), 'date': self.date
            }
        else:
            return _('New document')

    class Meta:
        ordering = ['-date',]
        abstract = True

    def save(self, **kwargs):
        self.date = self.date or datetime.datetime.now().date()
        super(AbstractDocumentDate, self).save(**kwargs)

class AbstractDocumentDateTime(models.Model):
    """ Абстрактная модель датированных документов, включающих время """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    date_time = models.DateTimeField(
            null=True, blank=True,
            verbose_name = _("date and time"))

    def __unicode__(self):
        if self.pk:
            doc = self._meta.verbose_name.split(' ')
            doc[0] = doc[0].title()
            return _('%(document)s from %(date)s') % {
                'document': ' '.join(doc),
                'date': dateformat.format(self.date_time,
                    'Y-m-d H:i:s') if self.date_time else 'None'
            }
        else:
            return _('New document')

    class Meta:
        ordering = ['-date_time']
        abstract = True

    def save(self, **kwargs):
        self.date_time = self.date_time or datetime.datetime.now()
        super(AbstractDocumentDateTime, self).save(**kwargs)

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

class AbstractGroupText(models.Model):
    """ Абстрактная модель группы или категории с длинным полем"""
    title = models.TextField(
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

class AbstractHierarchy(models.Model):
    """ Абстрактная модель иерархического списка.

        Сделано на примере пунктов в офисной документации
        1. - Каталог первого уровня
          1. - Объект в каталоге первого уровня
          1. - Объект в каталоге первого уровня
          1.1. - Каталог второго уровня
            1.1.- Объект в каталоге второго уровня
            1.1.- Объект в каталоге второго уровня
            1.1.1 - Каталог третьего уровня
        2. - Каталог первого уровня
          2.1. - Каталог второго уровня
            2.1.1 - Каталог третьего уровня
        
        Для нормального функционирования дочерним таблицам нужно
        добавить 3 обязательных поля:

        path = models.CharField(
            max_length=512, # Оптимальный вариант с большим запасом
            editable=False, # Измените это по желанию
            blank=True,
            verbose_name = _('path'))
        counter = models.IntegerField(
            editable=False, # Измените это по желанию
            null=True, blank=True,
            verbose_name = _('counter'))
        container = models.ForeignKey(
            "<CLASS_NAME>", # Обязательно измените это!!!
            #limit_choices_to={'is_container': True}, # Если есть 4-е поле
            related_name="only_nested_objects_set", # Не изменяйте это!!!
            null=True, blank=True,
            verbose_name = _('container'))
        
        И 4-е, если таблица будет содержать не только контейнеры, но и
        простые предметы:

        is_container = models.BooleanField(
            default=False, # Измените это по желанию
            verbose_name=_('is container'))
    
    """
    SEPARATOR = '.'

    title = models.CharField(
            max_length=255,
            verbose_name = _('title'))

    path         = lambda: NotImplemented
    counter      = lambda: NotImplemented
    container    = lambda: NotImplemented
    is_container = True


    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['path', 'title']
        abstract = True

    def get_nested_objects(self, recursive=True):
        """ Возвращаем все вложенные объекты """
        if recursive and self.path:
            return filterQueryset(self._default_manager, ['^path'], self.path)
        else:
            return self.only_nested_objects_set.all()

    def get_nested_containers(self, recursive=True):
        """ Возвращаем все вложенные контейнеры """
        return self.get_nested_objects(
                recursive=recursive).filter(is_container=True)

    def get_nested_items(self, recursive=True):
        """ Возвращаем все вложенные предметы """
        return self.get_nested_objects(
                recursive=recursive).filter(is_container=False)

    def save_path(self):
        """ Устанавливаем путь """
        # Обработка предметов
        if not self.is_container:
            if self.container:
                self.path = self.container.path
            return self.path

        # Обработка контейнеров
        old_container = old_path = None
        if self.pk:
            old = self._default_manager.get(pk=self.pk)
            old_container = old.container
            old_path = old.path
        # При ручном пользовательском исправлении пути ничего не делаем
        if self.pk and self.container == old_container and self.path != old.path:
            return self.path
        # Вычисление пути
        if self.container:
            _path = self.container.path
            counter = self.container.counter + 1
            self._default_manager.filter(pk=self.container.pk).update(counter=counter)
        else:
            _path = ''
            # Для корневых пунктов нет счётчика, поэтому вычисляем
            # его значение
            roots = self._default_manager.filter(container__isnull=True)
            counter = roots.count() + 1
            root_digits = [ int(x.path.split(self.SEPARATOR)[0]) for x in roots ]
            while counter in root_digits:
                counter += 1
        self.path = '%s%s%s' % (_path, counter, self.SEPARATOR)

        return self.path

    def save(self, **kwargs):
        """ При сохранении объекта нужно установить путь """
        self.save_path()
        super(AbstractHierarchy, self).save(**kwargs)

class AbstractPathBase(models.Model):
    """ Класс для общих методов моделей иерархических путей """
    title        = ''
    parent_path  = ''
    is_container = True

    def __unicode__(self):
        return self.title

    class Meta:
        abstract = True

    def get_parent_path(self, from_parents=False):
        parent_path = self.parent_path
        if from_parents:
            parent_path = ''
            if self.parent:
                parent_path = self.parent.get_object_path(
                    from_parents=from_parents)
        return parent_path

    def set_parent_path(self, from_parents=False):
        self.parent_path = self.get_parent_path(from_parents=from_parents)
        return self.parent_path

    @property
    def field_key_prepared(self):
        return str(self.pk).replace(os.path.sep, '_')

    def get_parents(self):
        L = []
        root = self
        while root:
            if not root.parent:
                break
            root = root.parent
            L.insert(0, root)
        return L

    def get_object_path(self, from_parents=False):
        self.set_parent_path(from_parents=from_parents)
        return os.path.join(self.parent_path, self.field_key_prepared)

    def get_root(self):
        """ Возвращаем корневого родителя """
        root = self
        while root:
            if not root.parent:
                break
            root = root.parent
        return root

    def get_nested_objects(self):
        """ Возвращаем все вложенные объекты """
        return filterQueryset(self._default_manager,
                ['^parent_path'],
                self.get_object_path().rstrip(os.path.sep) \
                + os.path.sep)

    def get_nested_containers(self):
        """ Возвращаем все вложенные контейнеры """
        if hasattr(self, 'is_container') and \
        isinstance(self.is_container, models.BooleanField):
            return self.get_nested_objects().filter(is_container=True)
        return self.get_nested_objects()

    def get_nested_items(self):
        """ Возвращаем все вложенные предметы """
        if hasattr(self, 'is_container') and \
        isinstance(self.is_container, models.BooleanField):
            return self.get_nested_objects().filter(is_container=False)
        return self.get_nested_objects()

    def save_from_root(self):
        """ Сохраняем все элементы, начиная от корня """
        related_name = self.__class__.parent.field.related_query_name()
        def recursive(obj):
            for i in getattr(obj, related_name).all():
                i.save(from_root=False)
                for j in recursive(i):
                    yield j

        root = self.get_root()
        root.save(from_root=False)

        for obj in recursive(root):
            pass

        return True

    def save_parent_path(self):
        """ Сохраняем родительский путь и помечаем родителя
            как контейнер
        """
        self.set_parent_path(from_parents=True)
        if self.parent:
            if not self.parent.is_container:
                try:
                    self.parent.is_container = True
                    self.parent.save()
                except Exception as e:
                    print e

        return self.parent_path

    def save(self, from_root=True, **kwargs):
        """ При сохранении объекта нужно сохранить родительский путь """
        if from_root:
            self.save_from_root()
        else:
            self.save_parent_path()
        if self.parent:
            self._default_manager.filter(
                pk=self.parent.pk
            ).update(is_container=True)
        super(AbstractPathBase, self).save(**kwargs)

class AbstractPathByID(AbstractPathBase):
    """ Абстрактная модель иерархического списка, основанном на методе
        хранения родительского пути в отдельном поле.

        Сделано на примере каталогов в UNIX
        1       - Каталог первого уровня c идентификтором 1
        1/12    - Объект в каталоге первого уровня
        1/13    - Объект в каталоге первого уровня
        1/2     - Каталог второго уровня c идентификтором 2
        1/2/14  - Объект в каталоге второго уровня
        1/2/15  - Объект в каталоге второго уровня
        1/2/3   - Каталог третьего уровня c идентификтором 3
        4       - Каталог первого уровня c идентификтором 4
        4/5     - Каталог второго уровня c идентификтором 5
        4/5/6   - Каталог третьего уровня c идентификтором 6

        Для нормального функционирования дочерним таблицам нужно
        установить 1 обязательное поле:

        parent = models.ForeignKey(
            "<CLASS_NAME>", # Обязательно измените это!!!
            #limit_choices_to={'is_container': True}, # Если есть это поле
            null=True, blank=True,
            verbose_name = _('parent'))

        и одно необязательное, если таблица будет содержать не только
        контейнеры, но и простые предметы:

        is_container = models.BooleanField(
            default=False, # Измените это по желанию
            verbose_name=_('is container'))

    """
    parent_path = models.CharField(
            max_length=255,
            editable=False,
            blank=True,
            verbose_name = _('parent path'))
    title = models.CharField(
            max_length=255,
            verbose_name = _('title'))

    class Meta:
        ordering = ['parent_path', 'title']
        abstract = True

class AbstractPathByTitle(AbstractPathBase):
    """ Абстрактная модель иерархического списка, основанном на методе
        хранения родительского пути в отдельном поле.

        Сделано на примере каталогов в UNIX
        А                       - Каталог первого уровня
        А/Ананас                - Объект в каталоге первого уровня
        А/Арбуз                 - Объект в каталоге первого уровня
        А/Прочее                - Каталог второго уровня
        А/Прочее/Банан          - Объект в каталоге второго уровня
        А/Прочее/Яблоко         - Объект в каталоге второго уровня
        А/Прочее/Удалёнка       - Каталог третьего уровня
        Б                       - Каталог первого уровня
        Б/Бегемоты              - Каталог второго уровня
        Б/Бегемоты/Летающие     - Каталог третьего уровня
        Б/Бегемоты/Прочие       - Каталог третьего уровня

        Для нормального функционирования дочерним таблицам нужно
        установить 1 обязательное поле:

        parent = models.ForeignKey(
            "<CLASS_NAME>", # Обязательно измените это!!!
            #limit_choices_to={'is_container': True}, # Если есть это поле
            null=True, blank=True,
            verbose_name = _('parent'))

        и одно необязательное, если таблица будет содержать не только
        контейнеры, но и простые предметы:

        is_container = models.BooleanField(
            default=False, # Измените это по желанию
            verbose_name=_('is container'))

    """
    parent_path = models.CharField(
            max_length=500,
            editable=False,
            blank=True,
            verbose_name = _('parent path'))
    path = models.CharField(
            max_length=600,
            editable=False,
            blank=True,
            verbose_name = _('path'))
    title = models.CharField(
            max_length=100,
            verbose_name = _('title'))

    class Meta:
        ordering = ['path']
        abstract = True

    @property
    def field_key_prepared(self):
        return self.title.replace(os.path.sep,'_')

    def get_path_prepared_as_list(self):
        return self.path.split(os.path.sep)

    @property
    def path_prepared(self):
        pre = self.get_path_prepared_as_list()
        basename = pre.pop(-1)
        pre = [ '<b>-</b>' for x in pre ]
        if not self.parent:
            pre.append('<strong>'+basename+'</strong>')
        elif not self.is_container:
            pre.append('<em>'+basename+'</em>')
        else:
            pre.append(basename)
        return ' '.join(pre)

    def save(self, **kwargs):
        """ При сохранении объекта нужно сохранить собственный путь """
        self.path = self.get_object_path(from_parents=True)
        super(AbstractPathByTitle, self).save(**kwargs)

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
                            remove_file(name)
        super(AbstractImage, self).save(**kwargs)

    def delete(self, **kwargs):
        # delete files:
        for name in (
            self.image.path, self.image.thumb_path, 
            ):
            remove_file(name)
        super(AbstractImage, self).delete(**kwargs)

    class Meta:
        abstract = True

class AbstractFile(AbstractData):
    """ Абстрактная модель для файлов """
    default_label_type = u'%s' % _('file')
    file = models.FileField(upload_to=upload_to, 
            max_length=260,
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
                        remove_file(presave_obj.file.path)
        super(AbstractFile, self).save()

    def delete(self):
        remove_file(self.file.path)
        super(AbstractFile, self).delete()

    class Meta:
        abstract = True

class AbstractUserSettings(models.Model):
    """ Общая модель """
    user = models.ForeignKey(
            User,
            verbose_name=_('user'))
    json = fields.JSONField(
            blank=True,
            verbose_name = _('JSON value'))

    def __unicode__(self):
        return unicode(self.user)

    class Meta:
        abstract = True

    @property
    def value(self):
        return self.json
