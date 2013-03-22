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
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login as _login, logout as _logout, password_change, password_change_done
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.cache import add_never_cache_headers
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import Promise
from django.core.serializers.json import DjangoJSONEncoder

from decimal import Decimal

from quickapi.http import JSONResponse, JSONRedirect
from quickapi.views import api as _api
from quickapi.decorators import login_required, api_required

from bwp.sites import site
from bwp.forms import BWPAuthenticationForm
from bwp.conf import settings, ARRAY_FORM_OBJECT_KEY, ARRAY_FORM_COMPOSE_KEY
from bwp.utils.convertors import jquery_form_array, jquery_multi_form_array

from bwp.contrib.usersettings.models import OrgUserSettings, GlobalUserSettings

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

def get_json_response(content, **kwargs):
    """ Конструируем HttpResponse объект. """
    result = simplejson.dumps(content, ensure_ascii=False,
                                cls=DjangoJSONEncoder,
                                indent=4,
                            ).encode('utf-8', 'ignore')
    response = HttpResponse(
                mimetype="application/json",
                content_type="application/json",
                **kwargs)
    if len(result) > 512:
        response['Content-encoding'] = 'deflate'
        result = result.encode('zlib')
    response.write(result)
    add_never_cache_headers(response)
    return response

def datatables(request, model=None, info=None, serialize=True):
    """ Представление для работы с DataTables """
    ctx = {'DEBUG': settings.DEBUG}
    app_dict = {}
    user = request.user
    if not user.is_authenticated():
        return get_json_response(None)

    model_bwp = None
    if model or 'model' in request.REQUEST:
        model = request.REQUEST.get('model', model)
        model_bwp = site.bwp_dict(request).get(model)
    if model_bwp:
        if info or 'info' in request.REQUEST:
            if serialize:
                return get_json_response(model_bwp.datatables_get_info(request))
            return model_bwp.datatables_get_info(request)
        elif serialize:
            return get_json_response(model_bwp.datatables_get_data(request))
        return model_bwp.datatables_get_data(request)
    return get_json_response({'sError': 'No model'})

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
    if not 'bwp.contrib.usersettings' in settings.INSTALLED_APPS:
        return JSONResponse(status=405,
            message=u'Not "bwp.contrib.usersettings" in settings.INSTALLED_APPS')
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
def API_get_object(request, model, pk=None, **kwargs):
    """ *Возвращает экземпляр указанной модели.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"model"** - уникальное название модели, например: "auth.user".
        2. **"pk"** - первичный ключ объекта, если отсутствует, то вернётся пустой новый объект без pk 
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            TODO: написать
        }`
    """

    # Получаем модель BWP со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)

    # Возвращаем новый пустой объект или существующий 
    if pk is None:
        # Новый
        return model_bwp.new(request)
    else:
        # Существующий
        return model_bwp.get(request, pk)

@api_required
@login_required
def API_get_collection(request, model, compose=None, page=1, per_page=None,
    query=None, order_by=None, **kwargs):
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
    
    options = dict(request=request, page=page, query=query, 
                    per_page=per_page, order_by=order_by)
    
    # Возвращаем коллекцию композиции, если указано
    if compose:
        compose = model_bwp.compose_dict(**options)
        return compose.get(**options)

    # Возвращаем коллекцию в JSONResponse
    return model_bwp.get(**options)

@api_required
@login_required
def API_datatables_info(request, model, **kwargs):
    """ *Возвращает специализированные для Datatables.net данные.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"model"** - уникальное название модели, например: "auth.user".
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            TODO: расписать.
        }`
    """
    return JSONResponse(data=datatables(request, model, info=True, serialize=False))

QUICKAPI_DEFINED_METHODS = {
    'get_apps':         'bwp.views.API_get_apps',
    'get_settings':     'bwp.views.API_get_settings',
    'get_object':       'bwp.views.API_get_object',
    'get_collection':   'bwp.views.API_get_collection',
    'datatables_info':  'bwp.views.API_datatables_info',
}

@csrf_exempt
def api(request):
    return _api(request, QUICKAPI_DEFINED_METHODS)

########################################################################
#                             END API                                  #
########################################################################
