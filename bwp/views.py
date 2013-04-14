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
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login as _login, logout as _logout
#~ from django.contrib.auth.views import password_change, password_change_done
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.forms.models import modelform_factory

from quickapi.http import JSONResponse, JSONRedirect
from quickapi.views import index as quickapi_index
from quickapi.decorators import login_required, api_required

from bwp.sites import site
from bwp.forms import BWPAuthenticationForm
from bwp.conf import settings

from bwp import serializers

########################################################################
#                               PAGES                                  #
########################################################################
@never_cache
def index(request, extra_context={}):
    """
    Displays the main bwp index page, which lists all of the installed
    apps that have been registered in this site.
    """

    ctx = {'DEBUG': settings.DEBUG, 'title': _('bwp')}
    
    user = request.user
    if not user.is_authenticated():
        return redirect('bwp.views.login')
    ctx.update(extra_context)
    return render_to_response('bwp/index.html', ctx,
                            context_instance=RequestContext(request,))

@never_cache
def login(request, extra_context={}):
    """ Displays the login form for the given HttpRequest. """
    context = {
        'title': _('Log in'),
        'app_path': request.get_full_path(),
        REDIRECT_FIELD_NAME: redirect('bwp.views.index').get('Location', '/'),
    }
    context.update(extra_context)
    defaults = {
        'extra_context': context,
        'current_app': 'bwp',
        'authentication_form': BWPAuthenticationForm,
        'template_name': 'bwp/login.html',
    }
    return _login(request, **defaults)

@never_cache
def logout(request, extra_context={}):
    """ Logs out the user for the given HttpRequest.
        This should *not* assume the user is already logged in.
    """
    defaults = {
        'extra_context': extra_context,
        'template_name': 'bwp/logout.html',
    }
    return _logout(request, **defaults)

########################################################################
#                             END PAGES                                #
########################################################################
def get_form_instance(request, bwp_model, data=None, instance=None):
    """
    Возвращает экземпляр формы, которая используются для добавления
    или редактирования объекта.

    Аргумент `instance` является экземпляром модели `model_name`
    (принимается только если эта форма будет использоваться для
    редактирования существующего объекта).
    """
    model = bwp_model.model
    defaults = {}
    if bwp_model.form:
        defaults['form'] = bwp_model.form
    if bwp_model.fields:
        defaults['fields'] = bwp_model.fields
    return modelform_factory(model, **defaults)(data=data, instance=instance)

def get_instance(request, pk, model_name):
    """ Возвращает зкземпляр указаной модели """
    model = site.model_dict(request).get(model_name)
    return model.objects.get(pk=pk)

########################################################################
#                               API                                    #
########################################################################

@api_required
@login_required
def API_get_settings(request):
    """ *Возвращает настройки пользователя.*
        
        ##### ЗАПРОС
        Без параметров.
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `
        - возвращается словарь с ключами из установленных настроек.
        `
    """
    user = request.user
    session = request.session
    us = {}
    return JSONResponse(data=us)

@api_required
@login_required
def API_get_apps(request, device=None, **kwargs):
    """ *Возвращает список из доступных приложений и их моделей.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"device"** - название устройства для которого есть
            доступные приложения (нереализовано).
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            TODO: написать
        }`
    """
    data=site.serialize(request)
    if not data:
        return JSONResponse(message=403)
    return JSONResponse(data=data)

@api_required
@login_required
def API_get_object(request, model, pk=None, copy=None, clone=None, **kwargs):
    """ *Возвращает экземпляр указанной модели.*

        ##### ЗАПРОС
        Параметры:
        
        1. **"model"** - уникальное название модели, например:
                        "auth.user".
        2. **"pk"**    - первичный ключ объекта, если отсутствует, то
                        вернётся пустой новый объект (тоже без pk).
        3. **"copy"**  - если задано, то возвращается простая копия
                        объекта (без pk).
        4. **"clone"**  - если задано и допустимо выполнять такую
                        операцию, то возвращается абсолютная копия
                        объекта (включая новый pk и копии m2m полей). 

        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            TODO: написать
        }`
    """

    # Получаем модель BWP со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)

    # Возвращаем новый пустой объект или существующий (либо его копию)
    if not pk:
        # Новый
        return model_bwp.new(request)
    else:
        if copy or clone:
            # Копия
            return model_bwp.copy(request, pk, clone)
        # Существующий
        return model_bwp.get(request, pk)

@api_required
@login_required
def API_get_collection(request, model, pk=None, compose=None, page=1,
    per_page=None, query=None, order_by=None, fields=None, **kwargs):
    """ *Возвращает коллекцию экземпляров указанной модели.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"model"** - уникальное название модели, например: "auth.user";
        2. **"compose"** - уникальное название модели Compose, 
            объекты которой должны быть возвращены: "group_set",
            по-умолчанию не используется;
        3. **"page"** -  номер страницы, по-умолчанию == 1;
        4. **"per_page"** - количество на странице, по-умолчанию определяется BWP;
        5. **"query"** - поисковый запрос;
        6. **"order_by"** - сортировка объектов.
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            'count': 2,
            'end_index': 2,
            'has_next': false,
            'has_other_pages': false,
            'has_previous': false,
            'next_page_number': 2,
            'num_pages': 1,
            'number': 1,
            'object_list': [
                {
                    'fields': {'first_name': u'First'},
                    'model': u'auth.user',
                    'pk': 1
                },
                {
                    'fields': {'first_name': u'Second'},
                    'model': u'auth.user',
                    'pk': 2
                }
            ],
            'previous_page_number': 0,
            'start_index': 1
        }`
    """

    # Получаем модель BWP со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)
    
    options = {
        'request': request,
        'page': page,
        'query': query,
        'per_page': per_page,
        'order_by': order_by,
        'fields': fields,
        'pk':pk, 
    }
    
    # Возвращаем коллекцию композиции, если указано
    if compose:
        dic = model_bwp.compose_dict(request)
        compose = dic.get(compose)
        return compose.get(**options)

    # Возвращаем коллекцию в JSONResponse
    return model_bwp.get(**options)

@api_required
@login_required
@transaction.commit_manually
def API_commit(request, objects, **kwargs):
    """ *Сохрание и/или удаление переданных объектов.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"objects"** - список объектов для изменения;
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `Boolean`
    """
    if not objects:
        transaction.rollback()
        return JSONResponse(data=False, status=400, message=unicode(_("List objects is blank!")))
    model_name = bwp = None
    try:
        for item in objects:
            # Уменьшение ссылок на объекты, если они существуют
            # в прошлой ротации
            if model_name != item['model']:
                model_name = item['model']
                bwp = site.bwp_dict(request).get(model_name)
            action = item['action'] # raise AttributeError()
            for name, val in item['fields'].items():
                if isinstance(val, list):
                    L = []
                    flag = False
                    for i in val:
                        if isinstance(i, list) and len(i) == 2:
                            L.append(i[0])
                            flag = True
                        else:
                            item['fields'][name] = i
                            break
                    if flag:
                        item['fields'][name] = L
            data = item['fields']
            # Новый объект
            if not item.get('pk', False):
                if bwp.has_add_permission(request):
                    form = get_form_instance(request, bwp, data=data)
                    if form.is_valid():
                        object = form.save()
                        bwp.log_addition(request, object)
                    else:
                        transaction.rollback()
                        return JSONResponse(status=400, message=unicode(form.errors))
            # Удаляемый объект
            elif action == 'delete':
                instance = get_instance(request, item['pk'], item['model'])
                if bwp.has_delete_permission(request, instance):
                    bwp.log_deletion(request, instance, unicode(instance))
                    instance.delete()
            # Обновляемый объект
            elif action == 'change': # raise AttributeError()
                instance = get_instance(request, item['pk'], item['model'])
                if bwp.has_change_permission(request, instance):
                    form = get_form_instance(request, bwp, data=data, instance=instance)
                    if form.is_valid():
                        object = form.save()
                        fix = item.get('fix', {})
                        bwp.log_change(request, object, ', '.join(fix.keys()))
                    else:
                        transaction.rollback()
                        return JSONResponse(status=400, message=unicode(form.errors))

    except Exception as e:
        transaction.rollback()
        if settings.DEBUG:
            return JSONResponse(status=500, message=unicode(vars()))
        raise e
    else:
        transaction.commit()
    return JSONResponse(data=True, message=unicode(_("Commited!")))

QUICKAPI_DEFINED_METHODS = {
    'get_apps':         'bwp.views.API_get_apps',
    'get_settings':     'bwp.views.API_get_settings',
    'get_object':       'bwp.views.API_get_object',
    'get_collection':   'bwp.views.API_get_collection',
    'commit':           'bwp.views.API_commit',
}

@csrf_exempt
def api(request):
    return quickapi_index(request, QUICKAPI_DEFINED_METHODS)

########################################################################
#                             END API                                  #
########################################################################
