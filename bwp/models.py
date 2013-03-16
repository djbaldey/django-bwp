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
from django.utils.translation import ugettext, ugettext_lazy as _ 
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.admin.util import quote
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
#~ from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import redirect

from copy import deepcopy

from bwp import serializers
from bwp.utils.filters import filterQueryset
from bwp.conf import settings
from bwp.widgets import get_widget_from_field

ADDING = 1
CHANGE = 2
DELETE = 3

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
        if self.action_flag == ADDITION:
            return _('Added "%(object)s".') % {'object': self.object_repr}
        elif self.action_flag == CHANGE:
            return _('Changed "%(object)s" - %(changes)s') % {'object': self.object_repr, 'changes': self.change_message}
        elif self.action_flag == DELETION:
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

    list_display = ('__unicode__', 'pk')
    list_display_css = {'pk': 'input-micro', 'id': 'input-micro'} # by default
    show_column_pk = False

    fields = None
    fieldsets = None
    widgets = None
    widgetsets = None
    search_fields = ()
    
    ordering = None
    actions = []
    
    paginator = Paginator

    @property
    def opts(self):
        if self.model is None:
            raise NotImplementedError('Set the "model" in %s.' % self.__class__.__name__)
        return self.model._meta
    
    def get_fields(self):
        """ Возвращает реальные объекты полей """
        if self.fields:
            return [ self.opts.get_field_by_name(name)[0] for name in self.fields ]
        else:
            return [ _tuple[0] for _tuple in self.opts.get_fields_with_model() ]

    def prepare_widget(self, field_name):
        """ Возвращает виджет с заменой атрибутов, согласно настроек
            текущего класса.
        """
        dic = dict([ (field.name, field) for field in self.get_fields() ])
        dic['pk'] = self.opts.pk
        widget = get_widget_from_field(dic[field_name])
        if not widget.is_configured:
            if self.list_display_css.has_key(field_name):
                new_class = '%s %s' % (widget.attr.get('class', ''), self.list_display_css[field_name])
                widget.attr.update({'class': new_class})
                widget.is_configured = True
        return widget
    
    def set_widgets(self):
        """ Устанавливает и возвращает виджеты. """
        self.widgets = [ self.prepare_widget(field.name) for field in self.get_fields() ]
        return self.widgets
    
    def get_widgets(self):
        """ Возвращает виджеты. """
        return self.widgets or self.set_widgets()
    
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

    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def queryset(self):
        return self.model._default_manager.get_query_set()

    def get_ordering(self, request):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)

    def order_queryset(self, request, qs=None):
        """
        Сортировка определённого, либо общего набора данных.
        """
        if qs is None:
            qs = self.queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        Can be overriden by the user in subclasses.
        """
        opts = self.opts
        return request.user.has_perm(opts.app_label + '.' + opts.get_add_permission())

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overriden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self.opts
        return request.user.has_perm(opts.app_label + '.' + opts.get_change_permission())

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overriden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `obj`
        model instance. If `obj` is None, this should return True if the given
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
    
    def __init__(self, related_name, related_model, bwp_site):
        self.related_name  = related_name
        self.related_model = related_model
        self.bwp_site = bwp_site
        if self.verbose_name is None:
            self.verbose_name = self.opts.verbose_name_plural or self.opts.verbose_name

    def get_data(self, obj):
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
        related_model_name = str(obj._meta)
        model = str(self.opts)
        html_id = ('%s.%s.%s' % (related_model_name, obj.pk, self.related_name)
            ).replace('.','-')
        data = {
            'label': capfirst(unicode(self.verbose_name)),
            'model': model, 'html_id': html_id,
            'related_model': related_model_name,
            'related_object': obj.pk,
        }

        # Permissions
        permissions = 'NOT IMPLEMENTED'

        # Widgets
        widgets = [ self.prepare_widget('pk') ]
        widgets.extend(self.get_widgets())
        widgets = [ widget.get_dict() for widget in widgets ]

        # Objects
        objects = getattr(obj, self.related_name)
        objects = objects.select_related().all() #TODO: сделать паджинатор
        objects = serializers.serialize('python', objects, use_natural_keys=True)

        data.update({'widgets': widgets, 'objects': objects,
                    'permissions': permissions })
        return data

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

    def get_compose_instances(self, request=None):
        compose_instances = []
        if not self.compositions:
            pass
        for related_name, compose_class in self.compositions:
            compose = compose_class(related_name, self.model, self.bwp_site)
            if request:
                if not (compose.has_add_permission(request) or
                        compose.has_change_permission(request) or
                        compose.has_delete_permission(request)):
                    continue
            compose_instances.append(compose)

        return compose_instances

    def object_to_python(self, pk):
        """ Python object with compositions and widgets(sets)
        """
        # Object
        obj = self.queryset().select_related().get(pk=pk)
        model = str(self.opts)
        html_id = ('%s.%s' %(model, obj.pk)).replace('.','-')
        data = serializers.serialize('python', [obj], use_natural_keys=True)[0]
        data.update({'label': unicode(obj), 'html_id': html_id})

        # Widgetsets
        widgetsets = []
        if self.fieldsets:
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

        # Widgets
        widgets = []
        if not self.fieldsets:
            widgets = [ widget.get_dict() for widget in self.get_widgets()]

        # Permissions
        permissions = 'NOT IMPLEMENTED'

        # Compositions
        compositions = []
        for compose in self.get_compose_instances():
            compositions.append(compose.get_data(obj))

        data.update({'widgets':widgets, 'widgetsets':widgetsets,
                    'permissions':permissions, 'compositions':compositions})
        return data

    def object_get(self, pk, user):
        return self.object_to_python(pk)

    def object_del(self, pk, user):
        qs = self.queryset()
        qs.all().filter(pk=pk).delete()
        return None

    def object_new(self, dict_form_object, post, user):
        qs = self.queryset()
        new = qs.create(**dict_form_object)
        return new

    def object_upd(self, pk, dict_form_object, post, user):
        qs = self.queryset()
        upd = qs.filter(pk=pk).update(**dict_form_object)
        return self.object_get(pk, user)

    def compose_upd(self, pk, array_form_compose, post, user):
        qs = self.queryset()
        return None

    def datatables_order_queryset(self, request, qs=None):
        """ Переопределённый метод базового класса. """
        # Number of columns that are used in sorting
        try:
            i_sorting_cols = int(request.REQUEST.get('iSortingCols', 0))
        except ValueError:
            i_sorting_cols = 0
        
        reserv = [ x for x in self.list_display if x not in ('__unicode__', '__str__')]

        ordering = []
        order_columns = self.list_display
        for i in range(i_sorting_cols):
            # sorting column
            try:
                i_sort_col = int(request.REQUEST.get('iSortCol_%s' % i))
            except ValueError:
                i_sort_col = 0
            # sorting order
            s_sort_dir = request.REQUEST.get('sSortDir_%s' % i)

            sdir = '-' if s_sort_dir == 'desc' else ''
            
            try:
                sortcol = order_columns[i_sort_col]
                if sortcol in ('__unicode__', '__str__'):
                    continue
            except:
                continue
            if isinstance(sortcol, list):
                for sc in sortcol:
                    ordering.append('%s%s' % (sdir, sc))
            else:
                ordering.append('%s%s' % (sdir, sortcol))
        
        if qs is None:
            qs = self.queryset()
        ordering = ordering or self.ordering or reserv
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def datatables_filter_queryset(self, request, qs=None):
        """ Returns a filtering QuerySet of all model instances. """
        if qs is None:
            qs = self.queryset()
        sSearch = request.REQUEST.get('sSearch', None)
        if sSearch:
            qs = filterQueryset(qs, self.search_fields, sSearch)
        return qs

    def datatables_pager_queryset(self, request, qs=None):
        if qs is None:
            qs = self.queryset()
        limit = min(int(request.REQUEST.get('iDisplayLength', 25)), 100)
        start = int(request.REQUEST.get('iDisplayStart', 0))
        offset = start + limit
        return qs[start:offset]

    def datatables_prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        display = self.list_display
        data = [ [ serialize_field(item, field) for field in display ] for item in qs ]
        return data

    def datatables_get_data(self, request):

        qs = self.queryset()

        # number of records before filtering
        total_records = qs.count()

        qs = self.datatables_filter_queryset(request, qs)

        # number of records after filtering
        total_display_records = qs.count()

        qs = self.datatables_order_queryset(request, qs)
        qs = self.datatables_pager_queryset(request, qs)

        # prepare output data
        aaData = self.datatables_prepare_results(qs)

        return {
            'sEcho': int(request.REQUEST.get('sEcho', 0)),
            'iTotalRecords': total_records,
            'iTotalDisplayRecords': total_display_records,
            'aaData': aaData
        }

    def datatables_get_info(self, request):
        meta = self.opts
        list_display = []
        # принудительная установка первичного ключа в начало списка
        # необходима для чёткого определения его на клиенте
        if self.list_display[0] != 'pk':
            self.list_display = ('pk',) + self.list_display
        list_display_css = {}
        # Словари параметров колонок
        not_bSortable = {"bSortable": False, "aTargets": [ ]}
        not_bVisible = {"bVisible": False, "aTargets": [ ]}
        for i, it in enumerate(self.list_display):
            if it in ('__unicode__', '__str__'):
                field = (capfirst(unicode(meta.verbose_name)),
                        capfirst(ugettext('object')))
                # Несортируемые колонки
                not_bSortable["aTargets"].append(i)
            elif it in ('pk', 'id'):
                field = ('#', capfirst(ugettext('identificator')))
                # Первичный ключ может отображаться, если это указано
                # явно в модели bwp
                if not self.show_column_pk and it == 'pk':
                    not_bVisible["aTargets"].append(i)
            else:
                f = meta.get_field_by_name(it)[0]
                field = (capfirst(unicode(f.verbose_name)),
                        capfirst(unicode(f.help_text or f.verbose_name)))
            list_display.append(field)
            list_display_css[field] = self.list_display_css.get(it, '')

        params = {
            'model': str(meta),
            'title': unicode(meta.verbose_name).title(),
        }
        temp_dict = params.copy()
        temp_dict["html_id"] = str(meta).replace('.', '-')
        temp_dict["columns"] = "".join([
            '<th data-toggle="tooltip" class="%s" title="%s">%s</th>' % (list_display_css[x], x[1], x[0])
            for x in list_display ])
        #~ temp_dict["tools"] = '<td colspan="%s">qwerty</td>' % len(temp_dict["columns"])
        html =  '<table id="table-model-%(html_id)s" data-model="%(model)s" '\
                'class="table table-condensed table-striped table-bordered table-hover">'\
                '<thead>'\
                    '<tr>%(columns)s</tr>'\
                '</thead>'\
                '<tbody></tbody>'\
                '</table>'
                #~ ' cellspacing="0" cellpadding="0" border="0" style="margin-left: 0px; width: 100%%;"' \

        return {
            'model':    params['model'],
            'title':    params['title'],
            'html_id':  temp_dict['html_id'],
            'perms':    self.get_model_perms(request),
            'html':     html % temp_dict,
            "oLanguage":    settings.LANGUAGE_CODE,
            "bProcessing":  True,
            "bServerSide":  True,
            "sAjaxSource":  redirect('bwp.views.datatables')['Location'],
            "sServerMethod":    "POST",
            "fnServerParams":   params.items(),
            "bLengthChange":    True,
            "sDom":         'lfrtip',
            "sScrollY":     None, # default
            "aoColumnDefs": [ not_bSortable, not_bVisible ],
        }
