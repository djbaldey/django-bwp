# -*- coding: utf-8 -*-
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

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext, Context, Template
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q
from django.template.defaultfilters import date as _date
#~ from django.contrib.auth.decorators import login_required
#~ from django.template.loader import get_template
#~ from django.utils import simplejson 
#~ from django.core import serializers
#~ from django.core.serializers.json import DjangoJSONEncoder
#~ from django.db import transaction
#~ from django.contrib.auth.models import User

import operator
import datetime

from models import *
import forms

#~ @login_required
def home(request):
    ctx = _default_ctx()
    return render_to_response('home.html', ctx,
                            context_instance=RequestContext(request,))

########################################################################
# START: БЛОК ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ
########################################################################

def _default_ctx(ctx={}):
    ctx['DEBUG'] = settings.DEBUG
    return ctx

def develop(request, **kwargs):
    ctx = _default_ctx()
    ctx.update({'kwargs': kwargs})
    return render_to_response('includes/_develop_site.html', ctx,
                            context_instance=RequestContext(request,))

### ФУНКЦИИ КОТОРЫХ НЕ ХВАТАЕТ В DJANGO ###

def print_debug(*args):
    if settings.DEBUG:
        print '-'*65 + '<<== DEBUG ==>>'
        for arg in args:
            print arg,
        print '\n' + '-'*61 + '<<== END DEBUG ==>>'

def get_object_or_none(qs, **kwargs):
    if type(qs) == type(models.Model):
        try:
            return qs.objects.get(**kwargs)
        except Exception as e:
            print_debug(e)
            return None
    try:
        return qs.get(**kwargs)
    except Exception as e:
        print_debug(e)
        return None

def filterQueryset(queryset, search_fields, query):
    """ Фильтрация """
    def construct_search(field_name):
        if field_name.startswith('^'):
            return "%s__istartswith" % field_name[1:]
        elif field_name.startswith('='):
            return "%s__iexact" % field_name[1:]
        elif field_name.startswith('@'):
            return "%s__search" % field_name[1:]
        else:
            return "%s__icontains" % field_name
    orm_lookups = [construct_search(str(search_field))
                   for search_field in search_fields]
    for bit in query.split():
        or_queries = [Q(**{orm_lookup: bit})
                      for orm_lookup in orm_lookups]
        queryset = queryset.filter(reduce(operator.or_, or_queries))
    
    if settings.DEBUG:
        try:
            print queryset.query
        except:
            try:
                print unicode(queryset.query)
            except:
                pass
    return queryset

def _get_paginator(qs, page=1, on_page=getattr(settings, 'OBJECTS_ON_PAGE', 25)):
    paginator = Paginator(qs, on_page)
    try:
        page_qs = paginator.page(int(page))
    except (EmptyPage, InvalidPage):
        page_qs = paginator.page(paginator.num_pages)
    return page_qs

def _get_datetime(string):
    def func(template):
        return datetime.datetime.strptime(string, template)
    T = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d") 
    for t in T:
        try:
            return func(t)
        except:
            pass
    return None
    
def _sortunique(container):
    L = list(set(container))
    L.sort()
    return L

########################################################################
# END: БЛОК ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ
########################################################################
