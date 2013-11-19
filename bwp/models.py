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
import django
from django.db import models, transaction
from django.db.models.fields.files import FileField, ImageField
from django.utils.translation import ugettext_lazy as _ 
from django.contrib.contenttypes.models import ContentType

from django.contrib.admin.util import quote
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.crypto import get_random_string
from django.core.paginator import Paginator, Page, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect

from django.http import (HttpResponseNotFound, HttpResponseBadRequest,
    HttpResponseForbidden)
from quickapi.http import JSONResponse

from copy import deepcopy
import os, datetime

from bwp.utils.convertors import serialize
from bwp.utils.http import get_http_400, get_http_403, get_http_404
from bwp.utils.filters import filterQueryset
from bwp.utils.classes import upload_to
from bwp.utils import print_debug

from bwp import conf, User, Group, Permission
from bwp.db import fields
from bwp.contrib.abstracts.models import AbstractUserSettings

SEARCH_KEY            = getattr(conf, 'SEARCH_KEY', 'query')
DEFAULT_SEARCH_FIELDS = getattr(conf, 'DEFAULT_SEARCH_FIELDS',
    (# Основные классы, от которых наследуются другие
        models.CharField,
        models.TextField
    )
)

class LogEntryManager(models.Manager):
    def log_action(self, user_id, content_type_id, object_id,
    object_repr, action_flag, message=None):
        e = self.model(None, user_id, content_type_id,
            smart_unicode(object_id), object_repr[:200],
            action_flag, message)
        e.save()

class LogEntry(models.Model):
    CREATE = 1
    UPDATE = 2
    DELETE = 3

    action_time = models.DateTimeField(_('action time'), auto_now=True)
    user = models.ForeignKey(User, related_name='bwp_log_set')
    content_type = models.ForeignKey(ContentType, blank=True, null=True, related_name='bwp_log_set')
    object_id = models.TextField(_('object id'), blank=True, null=True)
    object_repr = models.CharField(_('object repr'), max_length=200)
    action_flag = models.PositiveSmallIntegerField(_('action flag'))
    message = models.TextField(_('message'), blank=True)

    objects = LogEntryManager()

    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        db_table = 'bwp_log'
        ordering = ('-action_time',)

    def __repr__(self):
        return smart_unicode(self.action_time)

    def __unicode__(self):
        D = {'object': self.object_repr, 'message': self.message}
        if self.action_flag == LogEntry.CREATE:
            D['action'] = _('created').title()
        elif self.action_flag == LogEntry.UPDATE:
            D['action'] = _('updated').title()
        elif self.action_flag == LogEntry.DELETE:
            D['action'] = _('deleted').title()
        if self.action_flag in [LogEntry.CREATE, LogEntry.UPDATE, LogEntry.DELETE]:
            if self.change_message:
                return u'%(action)s «%(object)s» - %(message)s' % D
            else:
                return u'%(action)s «%(object)s»' % D

        return _('LogEntry Object')

    def is_create(self):
        return self.action_flag == LogEntry.CREATE

    def is_update(self):
        return self.action_flag == LogEntry.UPDATE

    def is_delete(self):
        return self.action_flag == LogEntry.DELETE

    def get_edited_object(self):
        "Returns the edited object represented by this log entry"
        return self.content_type.get_object_for_this_type(pk=self.object_id)

class TempUploadFile(models.Model):
    """ Временно загружаемые файлы для последующей
        передачи в нужную модель и требуемое поле
    """
    created = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to=upload_to, 
            verbose_name=_('file'))
    user = models.ForeignKey(
            User,
            null=True, blank=True,
            verbose_name=_('user'))
    
    def __unicode__(self):
        return self.file.name.split('/')[-1]

    class Meta:
        ordering = ('-created',)
        verbose_name = _('temporarily upload file')
        verbose_name_plural = _('temporarily upload files')

    def upload_to(self, filename):
        dic = {
            'tmp': conf.BWP_TEMP_UPLOAD_FILE,
            'filename': filename,
            'hash': get_random_string(conf.BWP_TEMP_UPLOAD_FILE_HASH_LENGTH),
        }
        return u'%(tmp)s/%(hash)s/%(filename)s' % dic
    
    def save(self, **kwargs):
        now = datetime.datetime.now()
        expires = now - datetime.timedelta(seconds=conf.BWP_TEMP_UPLOAD_FILE_EXPIRES)
        with transaction.commit_on_success():
            for x in TempUploadFile.objects.filter(created__lt=expires):
                x.delete()
            
        super(TempUploadFile, self).save(**kwargs)
    
    def delete(self, **kwargs):
        filename = self.file.path
        dirname  = os.path.dirname(filename)
        try:
            os.remove(filename)
            os.removedirs(dirname)
        except:
            pass
        super(TempUploadFile, self).delete(**kwargs)

def _replace_attname(value, fields=[]):
    """ Общий метод замены attname на name.
        Словари должны содержать ключ 'fields' или 'name'.
    """
    attnames = dict([ (x.attname, x.name) for x in fields if x.attname != x.name ])
    if not attnames:
        return value
    if isinstance(value, tuple):
        value = list(value)
    def _get_name(v):
        if isinstance(v, dict):
            if v.has_key('fields'):
                v['fields'] = _get_name(v['fields'])
            elif v.has_key('name'):
                v['name'] = _get_name(v['name'])
        elif isinstance(v, list):
            for i,s in enumerate(v):
                v[i] = _get_name(s)
        elif isinstance(v, (str, unicode)) and v in attnames:
            return attnames[v]
        return v
    return _get_name(value)

def _get_order_by(name, ordering):
    if name in ordering:
        return 'ASC'
    elif '-%s' % name in ordering:
        return 'DESC'
    return None

class BaseModel(object):
    """ Общие функции для ModelBWP, ComposeBWP, SelectorBWP. """

    site           = None
    icon           = None
    label          = None
    per_page       = 10
    per_page_min   = 5
    per_page_max   = 100
    coping         = True # разрешение копирования
    cloning        = None # разрешение клонирования

    column_default = '__unicode__'
    columns        = None

    fields              = None # по-умолчанию - все
    fields_set          = None # порядок, набор полей
    fields_exclude      = None # исключённые поля
    fields_search       = None # для запрета поиска пустой кортеж
    fields_html         = None # список полей с разметкой HTML
    fields_markdown     = None # список полей c разметкой Markdown
    fields_not_upgrade  = None # список полей с запретом повторного изменения
    fields_min          = None # словарь полей с минимальными значениями
    fields_max          = None # словарь полей с максимальными значениями
    fields_round        = None # словарь полей со значениями округления

    user_field          = None # если указано, то в это поле записывается
                               # Пользователь, производящий действия

    ordering            = None # список сортировки (по-умолчанию из модели)
    filters             = None # список фильтров (по-умолчанию нет)
    actions             = None # список действий (по-умолчанию ActionDelete)

    paginator           = Paginator

    def __init__(self, *args, **kwargs):
        # Установка значений по-умолчанию для изменяемых объектов
        self.columns             = self.columns             or ['__unicode__', 'pk']
        self.fields_set          = self.fields_set          or []
        self.fields_exclude      = self.fields_exclude      or []
        self.fields_html         = self.fields_html         or []
        self.fields_markdown     = self.fields_markdown     or []
        self.fields_not_upgrade  = self.fields_not_upgrade  or []
        self.fields_min          = self.fields_min          or {}
        self.fields_max          = self.fields_max          or {}
        self.fields_round        = self.fields_round        or {}

        super(BaseModel, self).__init__(*args, **kwargs)

    @property
    def opts(self):
        if self.model is None:
            raise NotImplementedError('Set the "model" in %s.' % self.__class__.__name__)
        return self.model._meta

    def _get_scheme(self):
        """ Возвращает жесткую схему для всех пользователей """
        if hasattr(self, '_SCHEME'):
            SCHEME = self._SCHEME.copy()
        else:
            SCHEME = {
                'icon':         self.icon,
                'label':        self.verbose_name,
                'has_cloning':  self.has_cloning,
                'has_coping':   self.has_coping,
                'per_page':     self.per_page,
                'per_page_min': self.per_page_min,
                'per_page_max': self.per_page_max,
            }
            SCHEME.update(self.scheme_fields)
            SCHEME.update(self.scheme_columns)
            SCHEME.update(self.scheme_row_rules)
            SCHEME.update(self.scheme_filters)
            SCHEME.update(self.scheme_summary)
            self._SCHEME = SCHEME.copy()
        return SCHEME

    def get_scheme(self, request):
        """ Возвращает динамическую схему модели, согласно прав пользователя """
        if request:
            perms = self.get_model_perms(request)
            if True not in perms.values():
                return False

        SCHEME = self._get_scheme()

        SCHEME.update(self.get_scheme_actions(request))
        SCHEME.update(self.get_scheme_compositions(request))
        SCHEME.update(self.get_scheme_reports(request))
        SCHEME.update(self.get_scheme_permissions(request))

        return SCHEME

    @property
    def has_coping(self):
        """ Проверяет, могут ли объекты копироваться """
        return bool(self.coping)

    @property
    def has_cloning(self):
        """ Проверяет, могут ли объекты клонироваться """
        if not hasattr(self, '_has_cloning'):
            if self.cloning is None:
                L = [ bool(self.opts.unique_together) ]
                L.extend([ f.unique for f in self.opts.local_fields if not f is self.opts.pk ])
                L.extend([ f.unique for f in self.opts.local_many_to_many ])
                self._has_cloning = not True in L
            else:
                self._has_cloning = self.cloning
        return self._has_cloning

    @property
    def verbose_name(self):
        return self.label or self.opts.verbose_name_plural

    @property
    def scheme_fields(self):
        """ Возвращает схему описания полей модели
        
            fields: {
                // Пример PrimaryKey и описание возможных атрибутов
                // прочих полей
                'id': {
                    'label': 'ID', // название поля
                    'type': 'int', // возможные типы:
                                   // int, int_list, float, decimal,
                                   // str, password, text, email, url, path,
                                   // html, markdown,
                                   // datetime, date, time, timedelta
                                   // file, image, bool, null_bool,
                                   // select, object, object_list
                    // необязательные поля:
                    'disabled': true, // общий режим редактирования
                    'not_upgrade': false, // не обновлять поле сохранённого объекта 
                    'hidden': true, // скрытое поле
                    'required': false, // обязательно к заполнению
                    'default': null, // значение по-умолчанию,
                                     // для дат это количество
                                     // секунд от текущего времени
                    'placeholder': null, // заполнитель поля
                    'help': null, // подсказка
                    'options': null, // для выбора из жесткого списка
                    'min': null, // минимальное значение
                    'max': null, // максимальное значение
                    'format': null, // формат вывода на экран
                                    // regexp, словарь или строка
                    'round': null,  // если == null, то не производить
                                    // округление, или указать разряд
                }
            },
            fields_set: [
                {
                    'label': 'Обязательные поля',
                    'fields':[
                        'is_active', 'title', 'count',
                    ],
                },
                'forein_key', 'many_to_many',
                ['created', 'file'],
            ],
            fields_search: ['title']
        """

        def check(f):
            if self.fields is None and not self.fields_exclude:
                return True
            elif self.fields and (
                f.attname in self.fields or f.name in self.fields):
                return True
            elif self.fields_exclude and (
                f.attname not in self.fields_exclude and \
                f.name not in self.fields_exclude):
                return True
            return False

        all_fields = [ x[0] for x in self.opts.get_fields_with_model() if check(x[0])]

        scheme = fields.get_scheme_fields(all_fields)
        for f in self.fields_html:
            scheme[f]['type'] = 'html'
        for f in self.fields_markdown:
            scheme[f]['type'] = 'markdown'
        for f in self.fields_not_upgrade:
            scheme[f]['not_upgrade'] = True
        for f,v in self.fields_min.items():
            scheme[f]['min'] = v
        for f,v in self.fields_max.items():
            scheme[f]['max'] = v
        for f,v in self.fields_max.items():
            scheme[f]['max'] = v

        fields_set = _replace_attname(self.fields_set, all_fields)
        self.fields_set = fields_set

        if not self.fields_search:
            fields_search = [
                '%s__icontains' % x[0].name for x in self.opts.get_fields_with_model() \
                if isinstance(x[0], tuple(DEFAULT_SEARCH_FIELDS))
            ]
            self.fields_search = fields_search

        return {'fields': scheme, 'fields_set': fields_set, 'fields_search': self.fields_search }

    @property
    def scheme_columns(self):
        """ Возвращает схему описания колонок таблицы.

            column_default: '__unicode__', // либо ['title', 'summa', ...]
            columns: [
                {'name': null, 'label': 'объект', 'ordering': false, 'order_by': null},
                {'name': 'is_active', 'label': 'активно', 'ordering': true, 'order_by': 'ASC'},
                {'name': 'select', 'label': 'пр.выбор', 'ordering': true, 'order_by': null},
                {'name': 'property_or_method', 'label': 'Свойство', 'ordering': false, 'order_by': null},
                {'name': 'id', 'label': 'ID', 'ordering': true, 'order_by': 'DESC'},
            ]
        """

        all_fields = [ x[0] for x in self.opts.get_fields_with_model() ]
        all_names = [ x.name for x in all_fields]
        column_default = _replace_attname(self.column_default, all_fields)
        columns = _replace_attname(self.columns, all_fields)
        ordering = self.get_ordering()

        for i,col in enumerate(columns):
            if not isinstance(col, dict):
                if col == '__unicode__':
                    columns[i] = {
                        'name': None,
                        'label': self.opts.verbose_name,
                        'ordering': False,
                        'order_by': None
                    }
                elif col == 'pk':
                    columns[i] = {
                        'name': 'pk',
                        'label': 'ID',
                        'ordering': True,
                        'order_by': _get_order_by(col, ordering)
                    }
                elif col in all_names:
                    columns[i] = {
                        'name': col,
                        'label': self.opts.get_field_by_name(col)[0].verbose_name,
                        'ordering': True,
                        'order_by': _get_order_by(col, ordering)
                    }
                else:
                    try:
                        # related fields
                        columns[i] = {
                            'name': col,
                            'label': self.opts.get_field_by_name(col)[0].verbose_name,
                            'ordering': True,
                            'order_by': _get_order_by(col, ordering)
                        }
                    except Exception as e:
                        raise e
            else:
                if col['name'] in all_names:
                    col['ordering'] = True
                    col['order_by'] = _get_order_by(col['name'], ordering)

        self.columns = columns
        self.column_default = column_default

        return {'column_default': column_default, 'columns': columns }

    @property
    def scheme_row_rules(self):
        """ Возвращает схему описания правил для строк в таблице
        
            rows_rules: {
                'is_active': {
                    'is_null': {'value': true, 'class': 'muted'},
                    'eq': {'value': false, 'class': 'danger'},
                },
                'created': {
                    'lt': {'value': '2013-10-10', 'class': 'muted'}, // парсинг даты
                    'eq': {'value': null, 'class': 'class_X'}, // null == new Date()
                    'gt': {'value': -3600, 'class': 'class_X'}, // new Date() - 3600 секунд
                    'range': {'value': ['2013-10-10', '2013-12-31'], 'class': 'class_X'}, 
                },
            },
            rows_rules_list: ['is_active', 'created']
        """
        # TODO: сделать
        return {'rows_rules': {}, 'rows_rules_list': []}

    @property
    def scheme_filters(self):
        """ Возвращает схему описания фильтров модели
        
            filters: {},
            filters_list: []
        """
        # TODO: сделать
        return {'filters': {}, 'filters_list': []}

    @property
    def scheme_summary(self):
        """ Возвращает схему описания суммарной информации, итогов

            summary: [
                {'name': 'total_summa', 'label': 'Итого'},
            ]
        """
        # TODO: сделать
        return {'summary': []}

    def get_scheme_actions(self, request):
        """ Возвращает схему описания доступных действий с наборами данных

            actions: {
                'delete': {'label': 'Удалить выбранные', 'confirm': true},
                'set_active': {'label': 'Сделать активными', 'confirm': false},
                'set_nonactive': {'label': 'Сделать неактивными', 'confirm': false},
            },
            actions_list: ['delete', 'set_active', 'set_nonactive']
        """
        # TODO: сделать
        return {'actions': {}, 'actions_list': []}

    def get_scheme_compositions(self, request):
        """ Возвращает схему описания композиций объектов

            compositions: {
                'secondmodel_set': {
                    icon: null,
                    label: 'Композиция второй модели',
                    app_name: 'tests',
                    model_name: 'secondmodel',
                    ...
                },
            },
            compositions_list: ['secondmodel_set']
        """
        # TODO: сделать
        return {'compositions': {}, 'compositions_list': []}

    def get_scheme_reports(self, request):
        """ Возвращает схему описания простых отчётов

            model_reports: [['model_report1', 'Отчёт №1'], ['model_report2', 'Отчёт №2']],
            object_reports: [['object_report1', 'Отчёт №1'], ['object_report2', 'Отчёт №2']]
        """
        # TODO: сделать
        return {'model_reports': [], 'object_reports': []}

    def get_scheme_permissions(self, request):
        """ Возвращает схему описания разрешений пользователя

            permissions: {
                'create': true, 'read': true, 'update': true, 'delete': true,
                'other': false,
            }
        """
        perms = self.get_model_perms(request)
        # TODO: сделать подгрузку дополнительных прав
        return {'permissions': perms}

    def get_ordering(self, request=None, **kwargs):
        """ Hook for specifying field ordering. """
        if self.ordering is None:
            return self.opts.ordering or ()
        return self.ordering







    def get_list_display(self):
        """ Устанавливает и/или возвращает список колонок списка
            объектов модели
        """
        if not hasattr(self, '_prepared_list_display'):
            new = []

            for obj in self.list_display:
                col = {'name':None,'label':None,'css':'','sorted':False}
                if   isinstance(obj, dict):
                    col.update(obj)
                elif isinstance(obj, (tuple, list)):
                    d = dict(zip(['name', 'label', 'css', 'sorted'], obj))
                    col.update(d)
                elif isinstance(obj, (str, unicode)):
                    name, label = obj, None
                    if label is None:
                        if name == '__unicode__':
                            label = self.opts.verbose_name
                        elif name in ('pk', 'id'):
                            label = _(name.upper())
                            col['sorted'] = True
                        elif name in self.dict_all_local_fields:
                            label = self.opts.get_field_by_name(name)[0].verbose_name
                            col['sorted'] = True
                        else:
                            label = _(name)
                    col['name'] = name
                    col['label'] = label
                # Перезапись ошибочного разрешения сортировки
                if not col['name'] in ('pk', 'id') and not col['name'] in self.dict_all_local_fields:
                    col['sorted'] = False
                # Обновление значения css
                if col['name'] in self.list_display_css:
                    col['css'] = self.list_display_css[col['name']]
                
                new.append(col)

            self.list_display = new
            self._prepared_list_display = True

        return self.list_display

    def get_search_fields(self):
        """ Устанавливает и/или возвращает значение полей поиска """
        if self.search_fields is None:
            self.search_fields = [
                x.name for x in self.get_fields_objects() if \
                    x.rel is None
            ]
        return self.search_fields

    @property
    def dict_all_local_fields(self):
        if hasattr(self, '_dict_all_local_fields'):
            return self._dict_all_local_fields

        self._dict_all_local_fields = dict([
            (field.name, field) for field in self.opts.local_fields
        ])
        return self._dict_all_local_fields

    def get_fields(self):
        """ Устанавливает и/или возвращает список полей объектов """
        if not self.fields:
            fields = [ field.name for field in self.opts.local_fields if field.editable ]
            self.fields = [ name for name in fields if name not in self.exclude ]
        return self.fields

    def get_fields_objects(self):
        """ Возвращает реальные объекты полей """
        return [ self.opts.get_field_by_name(name)[0] for name in self.get_fields() ]

    def get_file_fields(self):
        """ Устанавливает и/или возвращает список полей File/Image """
        if not self.file_fields:
            self.file_fields = [ name for name in self.get_fields() if \
                        isinstance(self.opts.get_field_by_name(name)[0],
                                                (FileField, ImageField))
                    ]
        return self.file_fields

    def get_filters(self):
        """ Возвращает словарь фильтров """
        def _get_filter(field):
            if isinstance(field, (str, unicode)):
                orign = field
                opts = self.opts
                fields = field.split('__')
                title = ''
                for f in fields:
                    field = opts.get_field_by_name(f)[0]
                    if field.rel:
                        title += unicode(field.verbose_name) + ': '
                        field = field.rel.get_related_field()
                        opts = field.model._meta
                    else:
                        title += unicode(field.verbose_name)
            else:
                orign = field.name
                title = unicode(field.verbose_name)
            return {
                'model': unicode(field.model._meta),
                'field': orign,
                'field_title': title,
                'widget': get_widget_from_field(field, True).get_dict(),
                }

        if self.filters is None:
            fields = self.opts.fields
            return [ _get_filter(x) for x in fields ]
        if isinstance(self.filters, (list, tuple)):
            return [ _get_filter(x) for x in self.filters ]
        return []

    def get_list_reports(self):
        L = []
        if 'bwp.contrib.reports' in conf.settings.INSTALLED_APPS:
            ct = ContentType.objects.get_for_model(self.model)
            docs = ct.document_set.all()
            for doc in docs:
                L.append({
                    'pk': doc.pk,
                    'title': doc.title,
                    'for_object': doc.for_object,
                })
        return L

    def prepare_widget(self, field_name):
        """ Возвращает виджет с заменой атрибутов, согласно настроек
            текущего класса.
        """
        dic = dict([ (field.name, field) for field in self.get_fields_objects() ])
        widget = get_widget_from_field(dic[field_name])
        if not widget.is_configured:
            if self.list_display_css.has_key(field_name):
                new_class = '%s %s' % (widget.attr.get('class', ''), self.list_display_css[field_name])
                widget.attr.update({'class': new_class})
                widget.is_configured = True
        return widget

    def set_widgets(self):
        """ Устанавливает и возвращает виджеты. """
        self.widgets = [ self.prepare_widget(field.name) for field in self.get_fields_objects() ]
        return self.widgets

    def get_widgets(self):
        """ Возвращает виджеты. """
        return self.widgets or self.set_widgets()

    def get_list_widgets(self):
        """ Возвращает виджеты в виде списка словарей, пригодного для JSON """
        return [ widget.get_dict() for widget in self.get_widgets() ]

    def set_widgetsets(self):
        """ Устанавливает и возвращает наборы виджетов. """
        if self.fieldsets:
            fieldsets = self.fieldsets
        else:
            fieldsets = (( None, { 'classes': '', 'fields': self.fields }), )
        self.widgetsets = []
        for label, dic in fieldsets:
            L = []
            dic = deepcopy(dic)
            if not dic['fields']:
                continue
            for group in dic['fields']:
                if isinstance(group, (tuple, list)):
                    L.append([ self.prepare_widget(field) for field in group ])
                else:
                    L.append(self.prepare_widget(group))
            dic['fields'] = L
            self.widgetsets.append((label, dic))
        return self.widgetsets

    def get_widgetsets(self):
        """ Возвращает наборы виджетов. """
        return self.widgetsets or self.set_widgetsets()

    def get_list_widgetsets(self):
        """ Возвращает наборы виджетов в виде списка, пригодного для JSON """
        widgetsets = []
        for label, dic in self.get_widgetsets():
            L = []
            dic = deepcopy(dic)
            for group in dic['fields']:
                if isinstance(group, (tuple, list)):
                    L.append([ widget.get_dict() for widget in group ])
                else:
                    L.append(group.get_dict())
            dic['fields'] = L
            widgetsets.append((label, dic))
        return widgetsets

    def get_instance(self, pk, model_name=None):
        """ Возвращает зкземпляр указаной модели, либо собственной """
        if model_name is None:
            model = self.model
        else:
            model = self.site.model_dict(model_name)
        return model.objects.get(pk=pk)

    def serialize(self, objects, **options):
        """ Сериализатор в объект(ы) Python, принимает либо один,
            либо несколько объектов или объект паджинации
            и точно также возвращает.
        """
        return serialize(objects, **options)

    def get_paginator(self, queryset, per_page=None, orphans=0, allow_empty_first_page=True, **kwargs):
        per_page = per_page or self.list_per_page
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def queryset_from_filters(self, queryset, filters, **kwargs):
        qs = queryset
        for f in filters:
            #~ print f
            if f.get('active', False):
                if f.get('inverse', False):
                    action = qs.exclude
                else:
                    action = qs.filter
                _type = f.get('type', 'exact')
                _field = f.get('field', 'id')
                if _type == 'blank':
                    orm_lookup = '%s__exact' % _field
                    bit = ''
                elif _type in ('in', 'range'):
                    orm_lookup = '%s__%s' % (_field, _type)
                    bit = f.get('values')
                    if not isinstance(bit, (list, tuple)):
                        bit = []
                    if _type == 'range' and len(bit) != 2:
                        bit = [None, None]
                else:
                    orm_lookup = '%s__%s' % (_field, _type)
                    try:
                        bit = f.get('values')[0]
                    except:
                        continue
                    if bit == '':
                        continue
                qs = action(models.Q(**{orm_lookup: bit}),)
        return qs

    def queryset(self, request=None, filters=[], **kwargs):
        qs = self.model._default_manager.get_query_set()
        if filters:
            qs = self.queryset_from_filters(qs, filters, **kwargs)
        return qs

    def order_queryset(self, request, queryset=None, ordering=None, **kwargs):
        """
        Сортировка определённого, либо общего набора данных.
        """
        
        if queryset is None:
            queryset = self.queryset()
        if ordering is None:
            ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def page_queryset(self, request, queryset=None, page=1, **kwargs):
        """
        Возвращает объект страницы паджинатора для набора объектов
        """
        queryset = self.order_queryset(request=request, queryset=queryset)
        paginator = self.get_paginator(queryset=queryset, **kwargs)

        # request может быть пустым
        try:
            page = int(request.REQUEST.get('page', page))
        except:
            pass
        try:
            page_queryset = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page_queryset = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page_queryset = paginator.page(paginator.num_pages)
        return page_queryset

    def get_search_query(self, request, search_key=None, **kwargs):
        """ Возвращает значение поискового запроса. """
        if search_key is None:
            return request.REQUEST.get(self.search_key, None)
        else:
            return request.REQUEST.get(search_key, None)

    def filter_queryset(self, request, queryset=None, query=None, fields=None, **kwargs):
        """ Возвращает отфильтрованный QuerySet для всех экземпляров модели. """
        if queryset is None:
            queryset = self.queryset(**kwargs)

        search_fields = self.get_search_fields()
        if fields and search_fields:
            fields = [ x for x in fields if x in search_fields ]
        else:
            fields = search_fields
        return filterQueryset(queryset, fields,
            query or self.get_search_query(request,**kwargs))

    def get_bwp_model(self, request, model_name, **kwargs):
        """ Получает объект модели BWP согласно привилегий """
        return self.site.bwp_dict(request).get(model_name)

    def get(self, request, pk=None, **kwargs):
        """ Получает объект согласно привилегий """
        if pk:
            try:
                object = self.queryset(request, **kwargs).get(pk=pk)
            except:
                return get_http_404(request)
            return self.get_object_detail(request, object, **kwargs)
        else:
            return self.get_collection(request, **kwargs)

    def get_object_detail(self, request, object, **kwargs):
        """
        Вызывается для окончательного формирования ответа сервера.
        """
        raise NotImplementedError

    def copy(self, request, pk, clone=None, **kwargs):
        """ Получает копию объекта согласно привилегий.
        """
        if self.has_create_permission(request):
            try:
                object = self.queryset(request, **kwargs).get(pk=pk)
            except:
                return get_http_404(request)
            return self.get_copy_object_detail(request, object, clone, **kwargs)
        else:
            return get_http_403(request)

    def get_copy_object_detail(self, request, object, clone, **kwargs):
        """
        Вызывается для окончательного формирования ответа сервера.
        """
        raise NotImplementedError

    def new(self, request, **kwargs):
        """
        Получает шаблон объекта согласно привилегий.
        """
        if self.has_create_permission(request):
            return self.get_new_object_detail(request, **kwargs)
        else:
            return get_http_403(request)

    def get_new_object_detail(self, request, **kwargs):
        """
        Вызывается для окончательного формирования ответа сервера.
        """
        raise NotImplementedError

    def get_collection(self, request, **kwargs):
        """ Метод может переопределяться, но по-умолчанию такой """
        qs = self.filter_queryset(request, **kwargs)
        qs = self.page_queryset(request, qs, **kwargs)
        total = self.get_queryset_total(qs)
        properties = [ x['name'] for x in self.get_list_display()\
            if not x['name'] in self.get_fields() ]
        data = self.serialize(qs, use_natural_keys=True, properties=properties)
        if total:
            data['total'] = total
        return JSONResponse(data=data)
    
    def get_queryset_total(self, qs):
        total = {}
        # TODO: доработать итоговые данные
        if self.sum_values:
            total['sum_values'] = {}
        if self.avg_values:
            total['avg_values'] = {}
        if self.min_values:
            total['min_values'] = {}
        if self.max_values:
            total['max_values'] = {}
        return total

    # Разрешения

    def has_read_permission(self, request):
        """
        Returns True if the given request has permission to read an object.
        """
        opts = self.opts
        return request.user.has_perm('%s.read_%s' % (opts.app_label, opts.model_name))

    def has_create_permission(self, request):
        """
        Returns True if the given request has permission to create an object.
        Can be overriden by the user in subclasses.
        """
        opts = self.opts
        return request.user.has_perm('%s.create_%s' % (opts.app_label, opts.model_name))

    def has_update_permission(self, request, object=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `object` parameter.

        Can be overriden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `object`
        model instance. If `object` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self.opts
        return request.user.has_perm('%s.update_%s' % (opts.app_label, opts.model_name))

    def has_delete_permission(self, request, object=None):
        """
        Returns True if the given request has permission to delete the given
        BWP model instance, the default implementation doesn't examine the
        `object` parameter.

        Can be overriden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `object`
        model instance. If `object` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self.opts
        return request.user.has_perm('%s.delete_%s' % (opts.app_label, opts.model_name))

    def get_model_perms(self, request):
        """
        Returns a dict of all perms for this model. This dict has the keys
        ``add``, ``change``, and ``delete`` mapping to the True/False for each
        of those actions.
        """
        return {
            'create': self.has_create_permission(request),
            'read':   self.has_read_permission(request),
            'update': self.has_update_permission(request),
            'delete': self.has_delete_permission(request),
        }

    # Логгирование

    def log_write(self, request, object, action, message):
        """ Запись в лог о действиях пользователя """
        if isinstance(object, LogEntry): return
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(object).pk,
            object_id       = object.pk,
            object_repr     = force_unicode(object),
            action_flag     = action,
            message         = message
        )

    def log_create(self, request, object, message=None):
        """ Запись о создании объекта """
        self.log_write(request=request, object=object,
            action=LogEntry.CREATE, message=message)

    def log_update(self, request, object, message=None):
        """ Запись об изменении объекта """
        self.log_write(request=request, object=object,
            action=LogEntry.UPDATE, message=message)

    def log_delete(self, request, object, message=None):
        """ Запись об удалении объекта """
        self.log_write(request=request, object=object,
            action=LogEntry.DELETE, message=message)


class ComposeBWP(BaseModel):
    """ Модель для описания вложенных объектов BWP. 
        multiply_fields = [ ('column_title', ('field_1', 'field_2')) ]
    """

    verbose_name = None
    related_name = None
    related_field = None
    is_many_to_many = False

    def __init__(self, related_name, related_model, bwp_site, model=None):
        if model:
            self.model = model
        self.related_name  = related_name
        self.related_model = related_model

        manager = getattr(related_model.model, related_name)
        if hasattr(manager, 'related'):
            field = manager.related.field
        else:
            field = manager.field
        self.related_field = field.name

        self.bwp_site = bwp_site
        if self.verbose_name is None:
            # TODO: сделать установку имени из поля
            self.verbose_name = self.opts.verbose_name_plural or self.opts.verbose_name

        super(ComposeBWP, self).__init__()

    def get_meta(self):
        """ Возвращает словарь метаданных об этой модели. """
        meta = dict([ (key, getattr(self, key)) for key in self.metakeys ])
        meta['widgets'] = self.get_list_widgets()
        meta['widgetsets'] = []
        meta['related_name'] = self.related_name
        meta['related_field'] = self.related_field
        meta['related_model'] = str(self.related_model.opts)
        meta['is_many_to_many'] = self.is_many_to_many
        meta['reports'] = self.get_list_reports()
        meta['filters'] = self.get_filters()
        meta['filters_dict'] = dict([ (x['field'], x) for x in meta['filters'] ])
        return meta

    def get(self, request, pk, **kwargs):
        """ Получает объекты согласно привилегий """
        return self.get_collection(request, pk, **kwargs)

    def get_collection(self, request, pk, **kwargs):
        """ Метод получения вложенных объектов """
        try:
            object = self.related_model.queryset(request).get(pk=pk)
        except:
            return get_http_404(request)
        qs = getattr(object, self.related_name).select_related().all()
        qs = self.queryset_from_filters(qs, **kwargs)
        qs = self.filter_queryset(request, qs, **kwargs)
        qs = self.page_queryset(request, qs, **kwargs)
        total = self.get_queryset_total(qs)

        properties = [ x['name'] for x in self.get_list_display()\
            if not x['name'] in self.get_fields() ]
        # Задаём использование натуральных ключей для того, чтобы не
        # ставился автоматически use_split_keys = True
        data = self.serialize(qs, use_natural_keys=True, properties=properties)
        if total:
            data['total'] = total
        return JSONResponse(data=data)

    def get_compose(self, request, object, **kwargs):
        """ Data = {
                'label': 'self.verbose_name',
                'model': 'self.model_name',
                'related_model': 'self.related_model name',
                'related_object': 'object.pk',
                'html_id': 'object_html_id + related_name',
                'perms':{'add':True, 'change':True, 'delete':True},
                'actions':[{<action_1>},{<action_2>}],
                'cols':[{col1},{col2}],
                'rows': [{row1}, {row2}]
            }
            colX = {
                'name': 'db_name',
                'hidden': False,
                'tag': 'input',
                'attr': {},
                'label': 'Название поля',
            }
            rowX = (
                ('real data value', 'frendly value'), # col1
                ('real data value', 'frendly value'), # col2
                ('real data value', 'frendly value'), # colX
            )
        """
        model = str(object._meta)
        compose = self.related_name
        data = {
            'model':    model,
            'pk':       object.pk,
            'compose':  compose,
            'label':    capfirst(unicode(self.verbose_name)),
            'meta':     self.meta,
        }

        # Permissions
        permissions = self.get_model_perms(request)

        # Widgets
        widgets = self.get_list_widgets()

        # Objects
        if object.pk:
            qs = getattr(object, self.related_name).select_related().all()
            qs = self.page_queryset(request, qs)
            objects = self.serialize(qs)
        else:
            objects = []

        data.update({'widgets': widgets, 'objects': objects,
                    'permissions': permissions })
        return data

class ManyToManyBWP(ComposeBWP):
    """ Расширение композиций для отображения полей m2m """
    is_many_to_many = True

    def add_objects_in_m2m(self, object, objects):
        m2m = getattr(object, self.related_name)
        m2m.add(*objects)
        return True

    def delete_objects_in_m2m(self, object, objects):
        m2m = getattr(object, self.related_name)
        m2m.remove(*objects)
        return True

class ModelBWP(BaseModel):
    """ Модель для регистрации в BWP.
        Наследуются атрибуты:
        __metaclass__ = forms.MediaDefiningClass
        raw_id_fields = ()
        fields = None
        exclude = None
        fieldsets = None
        form = forms.ModelForm
        filter_vertical = ()
        filter_horizontal = ()
        radio_fields = {}
        prepopulated_fields = {}
        formfield_overrides = {}
        readonly_fields = ()
        ordering = None
    """

    compositions = []
    
    def __init__(self, model, bwp_site):
        self.model = model
        self.bwp_site = bwp_site
        super(ModelBWP, self).__init__()

    def get_meta(self):
        """ Возвращает словарь метаданных об этой модели. """
        meta = dict([ (key, getattr(self, key)) for key in self.metakeys ])
        meta['compositions'] = [ x.get_meta() for x in self.compose_instances ]
        meta['widgets'] = self.get_list_widgets()
        meta['widgetsets'] = self.get_list_widgetsets()
        meta['reports'] = self.get_list_reports()
        meta['filters'] = self.get_filters()
        meta['filters_dict'] = dict([ (x['field'], x) for x in meta['filters'] ])
        return meta

    def prepare_meta(self, request):
        """ Обновляет информацию о метаданных согласно запроса """
        meta = deepcopy(self.meta)
        meta['compositions'] = [ x.get_model_info(request, bwp=False) for x in self.get_composes(request) ]
        return meta

    @property
    def compose_instances(self):
        """ Регистрирует экземпляры Compose моделей и/или возвращает их.
            При формировании первыми в композиции попадают поля
            ManyToMany, если же они переопределены, то заменяются.
        """
        if not hasattr(self, '_compose_instances'):
            L = []
            D = {}
            def add(cls, related_name, model=None):
                instance = cls(related_name=related_name, related_model=self,
                    bwp_site=self.bwp_site, model=model)
                D[related_name] = instance
                L.append(instance)

            for m2m in self.opts.local_many_to_many:
                related_name = m2m.related.field.get_attname()
                if related_name in self.exclude:
                    continue
                model = m2m.related.parent_model
                add(ManyToManyBWP, related_name, model)
            for related_name, compose_class in self.compositions:
                add(compose_class, related_name)

            self._compose_instances = [ D[x.related_name] for x in L ]
        return self._compose_instances
    
    def get_all_fields(self):
        m2m = [ x.related_name for x in self.compose_instances if x.is_many_to_many ]
        m2m.extend(self.fields or [])
        return m2m

    def get_object_detail(self, request, object, **kwargs):
        """ Метод возвращает сериализованный объект в JSONResponse """
        data = self.get_full_object(request, object)
        return JSONResponse(data=data)

    def get_copy_object_detail(self, request, object, clone, **kwargs):
        """ Метод возвращает сериализованную копию объекта в JSONResponse """
        pk = object.pk # save
        object.pk = None
        # Клонирование с созданием нового pk и заполнением полей m2m
        if clone and self.has_clone:
            object.save()
            oldobj = self.get_instance(pk=pk)
            self.log_addition(request, object, oldobj)
            for m2m in self.opts.local_many_to_many:
                old = getattr(oldobj, m2m.get_attname())
                new = getattr(object, m2m.get_attname())
                new.add(*old.all())
        data = self.get_full_object(request, object)
        return JSONResponse(data=data)

    def get_new_object_detail(self, request, **kwargs):
        """ Метод возвращает сериализованный, новый объект в JSONResponse """
        data = self.get_full_object(request, None, **kwargs)
        return JSONResponse(data=data)

    def get_full_object(self, request, object, filler={}, **kwargs):
        """ Python объект с композициями и виджетами(наборами виджетов). """
        # Object
        if isinstance(object, (str, int)):
            object = self.queryset().select_related().get(pk=object)
        elif not object:
            object = self.model()
            # TODO: made and call autofiller
            for field, value in filler.items():
                _field = self.opts.get_field_by_name(field)[0]
                if _field.rel:
                    value = _field.rel.to.objects.get(pk=value)
                setattr(object, field, value)
        model = str(self.opts)
        data = self.serialize(object)
        try:
            data['label'] = unicode(object)
        except:
            data['label'] = ''

        # Widgetsets
        widgetsets = self.get_list_widgetsets()

        # Widgets
        widgets = self.get_list_widgets()

        # Permissions
        permissions = self.get_model_perms(request)

        # Compositions
        compositions = []
        for compose in self.get_composes(request):
            compositions.append(compose.get_compose(request, object, **kwargs))

        data.update({'widgets':widgets, 'widgetsets':widgetsets,
                    'permissions':permissions, 'compositions':compositions})
        return data

    def get_composes(self, request=None):
        """ Получает список разрешённых моделей Compose. """
        compose_instances = []
        if self.compositions is None: # запрещены принудительно
            return compose_instances
        for compose in self.compose_instances:
            if request:
                # Когда все действия недоступны
                if not (compose.has_create_permission(request) or
                        compose.has_read_permission(request) or
                        compose.has_update_permission(request) or
                        compose.has_delete_permission(request)):
                    continue
            compose_instances.append(compose)
        return compose_instances

    def compose_dict(self, request, **kwargs):
        """
        Возвращает словарь, где ключом является имя модели Compose,
        а значением - сама модель, например:
            {'group_set': <Model Contacts.UserBWP> }
        """
        composes = self.get_composes(request)
        return dict([ (compose.related_name, compose) for compose in composes ])

class GlobalUserSettings(AbstractUserSettings):
    """ Глобальные настройки пользователей """
    class Meta:
        ordering = ['user',]
        verbose_name = _('global settings')
        verbose_name_plural = _('global settings')
        unique_together = ('user',)
