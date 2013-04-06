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
from django.db.models.query import QuerySet
from django.utils.translation import ugettext, ugettext_lazy as _ 
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.admin.util import quote
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.core.paginator import Paginator, Page, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect

from django.http import (HttpResponseNotFound, HttpResponseBadRequest,
    HttpResponseForbidden)
from quickapi.http import JSONResponse

from copy import deepcopy

from bwp import serializers
from bwp.utils.filters import filterQueryset
from bwp.conf import settings
from bwp.widgets import get_widget_from_field
from bwp.contrib.abstracts.models import AbstractUserSettings

ADDING = 1
CHANGE = 2
DELETE = 3

def is_api(request):
    return bool(request.path == redirect('bwp.views.api')['Location'])

def get_http_400(self, request):
    """ Если запрос на API, то возвращаем JSON, иначе обычный ответ """
    if is_api(request):
        return JSONResponse(status=400)
    return HttpResponseBadRequest()

def get_http_403(self, request):
    """ Если запрос на API, то возвращаем JSON, иначе обычный ответ """
    if is_api(request):
        return JSONResponse(status=404)
    return HttpResponseForbidden()

def get_http_404(self, request):
    """ Если запрос на API, то возвращаем JSON, иначе обычный ответ """
    if is_api(request):
        return JSONResponse(status=404)
    return HttpResponseNotFound()

def serialize_field(item, field, as_pk=False, with_pk=False, as_option=False):
    if field == '__unicode__':
        return unicode(item)
    else:
        val = getattr(item, field)
        if isinstance(val, models.Model):
            if as_pk:
                return val.pk
            elif as_option or with_pk:
                return (val.pk, unicode(val))
            return unicode(val)
        else:
            if as_option or as_pk:
                return None
            return val

class LogEntryManager(models.Manager):
    def log_action(self, user_id, content_type_id, object_id,
    object_repr, action_flag, change_message=''):
        e = self.model(None, None, user_id, content_type_id,
            smart_unicode(object_id), object_repr[:200],
            action_flag, change_message)
        e.save()

class LogEntry(models.Model):
    action_time = models.DateTimeField(_('action time'), auto_now=True)
    user = models.ForeignKey(User, related_name='bwp_log_set')
    content_type = models.ForeignKey(ContentType, blank=True, null=True, related_name='bwp_log_set')
    object_id = models.TextField(_('object id'), blank=True, null=True)
    object_repr = models.CharField(_('object repr'), max_length=200)
    action_flag = models.PositiveSmallIntegerField(_('action flag'))
    change_message = models.TextField(_('change message'), blank=True)

    objects = LogEntryManager()

    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        db_table = 'bwp_log'
        ordering = ('-action_time',)

    def __repr__(self):
        return smart_unicode(self.action_time)

    def __unicode__(self):
        if self.action_flag == ADDING:
            return _('Added "%(object)s".') % {'object': self.object_repr}
        elif self.action_flag == CHANGE:
            return _('Changed "%(object)s" - %(changes)s') % {'object': self.object_repr, 'changes': self.change_message}
        elif self.action_flag == DELETE:
            return _('Deleted "%(object)s."') % {'object': self.object_repr}

        return _('LogEntry Object')

    def is_addition(self):
        return self.action_flag == ADDING

    def is_change(self):
        return self.action_flag == CHANGE

    def is_deletion(self):
        return self.action_flag == DELETE

    def get_edited_object(self):
        "Returns the edited object represented by this log entry"
        return self.content_type.get_object_for_this_type(pk=self.object_id)

class BaseModel(object):
    """ Functionality common to both ModelBWP and ComposeBWP."""

    list_display        = ('__unicode__',)
    list_display_css    = {'pk': 'input-micro', 'id': 'input-micro'} # by default
    list_per_page       = 10
    list_max_show_all   = 200
    show_column_pk      = False

    fields              = None
    exclude             = []
    fieldsets           = None
    widgets             = None
    widgetsets          = None
    search_fields       = None # для запрета поиска пустой кортеж
    search_key          = 'query'

    ordering            = None
    actions             = []

    paginator           = Paginator
    form                = None
    site                = None
    hidden              = False
    allow_clone         = None
    
    # Набор ключей для предоставления метаданных об этой модели.
    metakeys = ('list_display', 'list_display_css', 'list_per_page',
                'list_max_show_all', 'show_column_pk', 'fields',
                'search_fields', 'search_key', 'ordering', 'has_clone',
                'hidden')

    @property
    def opts(self):
        if self.model is None:
            raise NotImplementedError('Set the "model" in %s.' % self.__class__.__name__)
        return self.model._meta

    def get_meta(self):
        """ Возвращает словарь метаданных об этой модели.
        
            Этот метод можно переопределить в наследуемом классе,
            например, чтобы добавить информацию из наследуемого класса
        """
        return dict([ (key, getattr(self, key)) for key in self.metakeys ])

    @property
    def meta(self):
        """ Регистрирует в словаре расширенную информацию о данной
            модели для клиента.
            
            Это свойство можно переопределить в наследуемом классе,
            например, чтобы добавить информацию из наследуемого класса
        """
        self.get_fields() # инициализация полей
        self.get_search_fields() # инициализация поисковых полей
        if not hasattr(self, '_meta'):
            self._meta = self.get_meta()
        return self._meta

    @property
    def has_clone(self):
        """ Проверяет, могут ли объекты клонироваться
        """
        if not hasattr(self, '_has_clone'):
            if self.allow_clone is None:
                L = [bool(self.opts.unique_together)]
                L.extend([ f.unique for f in self.opts.local_fields if not f is self.opts.pk ])
                L.extend([ f.unique for f in self.opts.local_many_to_many ])
                self._has_clone = not True in L
            else:
                self._has_clone = self.allow_clone
        return self._has_clone

    def prepare_meta(self, request):
        """ Обновляет информацию о метаданных согласно запроса """
        meta = deepcopy(self.meta)
        return meta

    def get_model_info(self, request, bwp=False):
        """ Информация о модели """
        dic = {
            'name':  unicode(self.opts),
            'label': capfirst(unicode(self.opts.verbose_name_plural)),
            'perms': self.get_model_perms(request),
            'meta':  self.prepare_meta(request),
        }
        if bwp:
            dic['bwp'] = self
        
        return dic

    def get_search_fields(self):
        """ Устанавливает и возвращает значение полей поиска """
        if self.search_fields is None:
            self.search_fields = [
                x.name for x in self.get_fields_objects() if \
                    x.rel is None
            ]
        return self.search_fields

    def get_fields(self):
        """ Устанавливает и возвращает значение полей объектов """
        if not self.fields:
            fields = [ field.name for field in self.opts.local_fields ]
            self.fields = [ name for name in fields if name not in self.exclude ]
        return self.fields

    def get_fields_objects(self):
        """ Возвращает реальные объекты полей """
        return [ self.opts.get_field_by_name(name)[0] for name in self.get_fields() ]

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
        if  not options.has_key('use_split_keys') \
        and not options.has_key('use_natural_keys'):
            options['use_split_keys'] = True # default
        if isinstance(objects, (QuerySet, Page, list, tuple)):
            # Список объектов
            data = serializers.serialize('python', objects, **options)
        else:
            # Единственный объект
            data = serializers.serialize('python', [objects], **options)[0]
        return data

    def get_paginator(self, queryset, per_page=None, orphans=0, allow_empty_first_page=True, **kwargs):
        per_page = per_page or self.list_per_page
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def queryset(self, request=None, **kwargs):
        return self.model._default_manager.get_query_set()

    def get_ordering(self, request=None, **kwargs):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)

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
        if self.has_add_permission(request):
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
        if self.has_add_permission(request):
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
        data = self.serialize(qs, use_natural_keys=True)
        return JSONResponse(data=data)

    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        Can be overriden by the user in subclasses.
        """
        opts = self.opts
        return request.user.has_perm(opts.app_label + '.' + opts.get_add_permission())

    def has_change_permission(self, request, object=None):
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
        return request.user.has_perm(opts.app_label + '.' + opts.get_change_permission())

    def has_delete_permission(self, request, object=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `object` parameter.

        Can be overriden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `object`
        model instance. If `object` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self.opts
        return request.user.has_perm(opts.app_label + '.' + opts.get_delete_permission())

    def get_model_perms(self, request):
        """
        Returns a dict of all perms for this model. This dict has the keys
        ``add``, ``change``, and ``delete`` mapping to the True/False for each
        of those actions.
        """
        return {
            'add': self.has_add_permission(request),
            'change': self.has_change_permission(request),
            'delete': self.has_delete_permission(request),
        }

    def log_addition(self, request, object):
        """
        Log that an object has been successfully added.

        The default implementation creates an bwp LogEntry object.
        """
        if isinstance(object, LogEntry): return
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(object).pk,
            object_id       = object.pk,
            object_repr     = force_unicode(object),
            action_flag     = ADDING
        )

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an bwp LogEntry object.
        """
        if isinstance(object, LogEntry): return
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(object).pk,
            object_id       = object.pk,
            object_repr     = force_unicode(object),
            action_flag     = CHANGE,
            change_message  = message
        )

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method is called
        before the deletion.

        The default implementation creates an bwp LogEntry object.
        """
        if isinstance(object, LogEntry): return
        LogEntry.objects.log_action(
            user_id         = request.user.id,
            content_type_id = ContentType.objects.get_for_model(self.model).pk,
            object_id       = object.pk,
            object_repr     = object_repr,
            action_flag     = DELETE
        )

class ComposeBWP(BaseModel):
    """ Модель для описания вложенных объектов BWP. 
        multiply_fields = [ ('column_title', ('field_1', 'field_2')) ]
    """

    verbose_name = None
    related_name = None
    is_many_to_many = False

    def __init__(self, related_name, related_model, bwp_site, model=None):
        if model:
            self.model = model
        self.related_name  = related_name
        self.related_model = related_model
        self.bwp_site = bwp_site
        if self.verbose_name is None:
            self.verbose_name = self.opts.verbose_name_plural or self.opts.verbose_name

    def get_meta(self):
        """ Возвращает словарь метаданных об этой модели. """
        meta = dict([ (key, getattr(self, key)) for key in self.metakeys ])
        meta['widgets'] = self.get_list_widgets()
        meta['widgetsets'] = []
        meta['related_name'] = self.related_name
        meta['related_model'] = str(self.related_model.opts)
        meta['is_many_to_many'] = self.is_many_to_many
        return meta

    def get(self, request, pk, **kwargs):
        """ Получает объекты согласно привилегий """
        return self.get_collection(request, pk, **kwargs)
    
    def get_collection(self, request, pk, **kwargs):
        """ Метод получения вложенных объектов """
        try:
            object = self.related_model.queryset(request, **kwargs).get(pk=pk)
        except:
            return get_http_404(request)
        qs = getattr(object, self.related_name).select_related().all()
        qs = self.filter_queryset(request, qs, **kwargs)
        qs = self.page_queryset(request, qs, **kwargs)
        data = self.serialize(qs)
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

    def get_meta(self):
        """ Возвращает словарь метаданных об этой модели. """
        meta = dict([ (key, getattr(self, key)) for key in self.metakeys ])
        meta['compositions'] = [ x.get_meta() for x in self.compose_instances ]
        meta['widgets'] = self.get_list_widgets()
        meta['widgetsets'] = self.get_list_widgetsets()
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
            for m2m in self.opts.local_many_to_many:
                old = getattr(oldobj, m2m.get_attname())
                new = getattr(object, m2m.get_attname())
                new.add(old.all())
        data = self.get_full_object(request, object)
        return JSONResponse(data=data)

    def get_new_object_detail(self, request, **kwargs):
        """ Метод возвращает сериализованный, новый объект в JSONResponse """
        data = self.get_full_object(request, None)
        return JSONResponse(data=data)

    def get_full_object(self, request, object, **kwargs):
        """ Python объект с композициями и виджетами(наборами виджетов). """
        # Object
        if isinstance(object, (str, int)):
            object = self.queryset().select_related().get(pk=pk)
        elif not object:
            object = self.model()
            # TODO: made and call autofiller
        model = str(self.opts)
        data = self.serialize(object)
        data['label'] = unicode(object)

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
                if not (compose.has_add_permission(request) or
                        compose.has_change_permission(request) or
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
