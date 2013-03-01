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
from django.core import serializers
from django.core.paginator import Paginator
from django.contrib.admin.options import BaseModelAdmin
from django.shortcuts import redirect

from copy import deepcopy

from bwp.utils.filters import filterQueryset
from bwp.conf import settings
from bwp.widgets import get_widget_from_field

ADDITION = 1
CHANGE = 2
DELETION = 3

def serialize_field(item, field, as_pk=False, with_pk=False):
    if field == '__unicode__':
        return unicode(item)
    else:
        val = getattr(item, field)
        if isinstance(val, models.Model):
            if as_pk:
                return val.pk
            elif with_pk:
                return (val.pk, unicode(val))
            return unicode(val)
        else:
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
        return self.action_flag == ADDITION

    def is_change(self):
        return self.action_flag == CHANGE

    def is_deletion(self):
        return self.action_flag == DELETION

    def get_edited_object(self):
        "Returns the edited object represented by this log entry"
        return self.content_type.get_object_for_this_type(pk=self.object_id)

class ComposeBWP(object):
    """ Модель для описания вложенных объектов BWP. 
        multiply_fields = [ ('column_title', ('field_1', 'field_2')) ]
    """
    model = None # обязательное
    list_display = ('__unicode__', 'pk')
    list_display_css = {'pk': 'input-micro', 'id': 'input-micro'} # by default
    
    object_fields = ()
    editable_fields = ()
    readonly_fields = ()
    multiply_fields = ()
    actions = []
    ordering = None
    verbose_name = None
    #~ form = forms.ModelForm
    #~ filter_vertical = ()
    #~ filter_horizontal = ()
    
    def __init__(self):
        if self.model is None:
            raise NotImplementedError('Set the "model" in %s.' % self.__class__.__name__)
        self.opts = self.model._meta
        if self.verbose_name is None:
            self.verbose_name = self.opts.verbose_name_plural or self.opts.verbose_name

class ModelBWP(BaseModelAdmin):
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
    
    list_display = ('__unicode__', 'pk')
    list_display_css = {'pk': 'input-micro', 'id': 'input-micro'} # by default
    show_column_pk = False
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    date_hierarchy = None
    save_as = False
    save_on_top = False
    paginator = Paginator
    compositions = []
    inlines = []
    
    # Custom templates (designed to be over-ridden in subclasses)
    add_form_template = None
    change_form_template = None
    change_list_template = None
    delete_confirmation_template = None
    delete_selected_confirmation_template = None
    object_history_template = None

    # Actions
    actions = []
    action_form = None
    actions_on_top = True
    actions_on_bottom = False
    actions_selection_counter = True

    def __init__(self, model, bwp_site):
        self.model = model
        self.opts = model._meta
        self.bwp_site = bwp_site
        self.fields_is_prepare = False
    
    def prepare_fields_and_fieldsets(self):
        if self.fields_is_prepare:
            return True
        #~ print 'prepare_fields_and_fieldsets'
        if self.fields:
            self.fields = [ self.opts.get_fields_by_name(name)[0] for name in self.fields ]
        else:
            self.fields = [ _tuple[0] for _tuple in self.opts.get_fields_with_model() ]

        dic = dict([ (field.name, field) for field in self.fields ])

        def prepare_widget(field_name):
            widget = get_widget_from_field(dic[field_name])
            if not widget.is_configured:
                if self.list_display_css.has_key(field_name):
                    new_class = '%s %s' % (widget.attr.get('class', ''), self.list_display_css[field_name])
                    widget.attr.update({'class': new_class})
                    widget.is_configured = True
            return widget

        # To list widgets
        self.fields = [ prepare_widget(field.name) for field in self.fields ]

        if self.fieldsets:
            for fs in self.fieldsets:
                new_fields = []
                for tuple_or_field in fs[1]['fields']:
                    if isinstance(tuple_or_field, (tuple, list)):
                        new_fields.append([ prepare_widget(name) for name in tuple_or_field])
                    else:
                        new_fields.append(prepare_widget(tuple_or_field))
                fs[1]['fields'] = new_fields

        self.fields_is_prepare = True
        return True
    
    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

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
            action_flag     = ADDITION
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
            action_flag     = DELETION
        )
    
    def get_ordering(self, request):
        """ Hook for specifying field ordering. """
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
        print ordering
        if ordering:
            return ordering
        return self.ordering or reserv

    def queryset(self):
        return self.model._default_manager.get_query_set()

    def filter_queryset(self, request, qs=None):
        """ Returns a filtering QuerySet of all model instances. """
        if qs is None:
            qs = self.queryset()
        sSearch = request.REQUEST.get('sSearch', None)
        if sSearch:
            qs = filterQueryset(qs, self.search_fields, sSearch)
        return qs
    
    def order_queryset(self, request, qs=None):
        if qs is None:
            qs = self.queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def pager_queryset(self, request, qs=None):
        if qs is None:
            qs = self.queryset()
        limit = min(int(request.REQUEST.get('iDisplayLength', 25)), 100)
        start = int(request.REQUEST.get('iDisplayStart', 0))
        offset = start + limit
        return qs[start:offset]

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        display = self.list_display
        data = [ [ serialize_field(item, field) for field in display ] for item in qs ]
        return data

    def object_as_data(self, pk):
        """ Data = {
                'model': 'app.model',
                'pk': 'pk',
                'html_id': 'app-model-pk',
                'fields':[({row1_field1},{row1_field2}),{row2_field3},{row3_field4}],
                'perms':{'add':True, 'change':True, 'delete':True},
                'comps':[{<compose_1>},{<compose_2>}]
            }
            Field = {
                'name': 'db_name',
                'hidden': False,
                'tag': 'input',
                'attr': {},
                'value': value,
                'label': 'Название поля',
            }
            Compose = {
                'model': 'app.model',
                'html_id': 'app-model',
                'columns':[('name', 'label'),],
                'perms':{'add':True, 'change':True, 'delete':True},
                'actions':[{<action_1>},{<action_2>}]
            }
        """

        self.prepare_fields_and_fieldsets()

        obj = self.queryset().select_related().get(pk=pk)
        model = str(self.opts)
        html_id = ('%s.%s' %(model, obj.pk)).replace('.','-')
        data = {'model': model, 'pk': obj.pk, 'html_id': html_id}
        data['raw_object'] = serializers.serialize('python', [obj])[0]

        def get_dict_widget(widget):
            dic = widget.get_dict()
            dic['value'] = serialize_field(obj, dic['name'], as_pk=True)
            return dic

        # Fields
        fields = []
        if self.fieldsets:
            fields = self.fieldsets
        else:
            fields = (( None, { 'classes': '', 'fields': self.fields }), )
        for f in fields:
            new_fields = []
            #~ f[1] = deepcopy(f[1]) # copy original dict with inner objects
            for tuple_or_widget in f[1]['fields']:
                if isinstance(tuple_or_widget, (tuple, list)):
                    new_fields.append([ get_dict_widget(widget) for widget in tuple_or_widget])
                else:
                    new_fields.append(get_dict_widget(tuple_or_widget))
            f[1]['fields'] = new_fields
        
        perms = 'NOT IMPLEMENTED'
        comps = []
        data.update({'fields':fields, 'perms':perms, 'comps':comps})
        for compose_model in self.compositions:
            cmodel = compose_model()
            all_fields = cmodel.opts.get_fields_with_model()
            #~ pkeys = getattr(obj,related_field).values_list('pk', flat=True).order_by('pk')
            #~ model_name = str(bwp_model.opts)
            #~ data[related_field]
            pass

        return data

    def new_object(self, post):
        qs = self.queryset()
        new = qs.create(**post)
        return new

    def get_context_data(self, request):

        qs = self.queryset()

        # number of records before filtering
        total_records = qs.count()

        qs = self.filter_queryset(request, qs)

        # number of records after filtering
        total_display_records = qs.count()

        qs = self.order_queryset(request, qs)
        qs = self.pager_queryset(request, qs)

        # prepare output data
        aaData = self.prepare_results(qs)

        return {
            'sEcho': int(request.REQUEST.get('sEcho', 0)),
            'iTotalRecords': total_records,
            'iTotalDisplayRecords': total_display_records,
            'aaData': aaData
        }

    def get_context_info(self, request):
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
            'model': str(meta)
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
