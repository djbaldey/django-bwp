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
from django.contrib.auth.views import login as _login, logout as _logout, \
    password_change, password_change_done
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

from bwp.contrib.usersettings.models import UserSettings

########################################################################
#                               PAGES                                  #
########################################################################
@never_cache
def index(request, extra_context={}):
    """
    Displays the main bwp index page, which lists all of the installed
    apps that have been registered in this site.
    """

    ctx = {'DEBUG': settings.DEBUG}
    
    user = request.user
    if not user.is_authenticated():
        return redirect('bwp.views.login')
    
    ctx.update({
        'title': _('bwp'),
        'app_list': site.app_list(request),
    })
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

def datatables(request):
    """ Представление для работы с DataTables """
    ctx = {'DEBUG': settings.DEBUG}
    app_dict = {}
    user = request.user
    if not user.is_authenticated():
        return get_json_response(None)

    model_bwp = None
    if 'model' in request.REQUEST:
        model = request.REQUEST.get('model')
        model_bwp = site.bwp_dict.get(model)
    if model_bwp:
        if 'info' in request.REQUEST:
            return get_json_response(model_bwp.datatables_get_info(request))
        return get_json_response(model_bwp.datatables_get_data(request))
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
        
        - возвращается словарь с ключами из установленных настроек.
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
def API_object_action(request, model, key, pk=None, **kwargs):
    """ *Производит действия с экземпляром(ми) указанной модели.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"model"** - уникальное название модели, например: "auth.user".
        2. **"key"** - действие ('view', 'add', 'change' либо 'remove').
        3. **"pk"** - первичный ключ объекта, если необходим.
        4. и далее: специализированные параметры (SP) для указанного действия.
        
        ##### ОТВЕТ
        Формат ключа **"data"**: зависит от выполняемой операции **"key"**.
        
        ##### СПИСОК ДЕЙСТВИЙ
        - **'get'** - возвращает объект (SP: отсутствует);
        - **'add'** - создаёт новый объект (SP: все нужные поля для заполнения);
        - **'set'** - изменяет существующий объект (SP: все нужные поля для заполнения);
        - **'del'** - удаляет объект (SP: отсутствует);
    """
    actions_with_pk = ('get', 'upd', 'del')
    session = request.session
    user = request.user
    dict_form_object, array_form_compose, data = None, None, None

    # Для django-quickapi.
    # Если данные передавались в едином JSON, то заменим словарь параметров
    post = request.POST
    if 'jsonData' in post:
        post = kwargs
        # Получение заполненных полей объектов
        if ARRAY_FORM_OBJECT_KEY in post:
            dict_form_object = jquery_form_array(post[ARRAY_FORM_OBJECT_KEY])
        elif ARRAY_FORM_COMPOSE_KEY in post:
            array_form_compose = jquery_multi_form_array(post[ARRAY_FORM_COMPOSE_KEY])

    model_bwp = site.bwp_dict.get(model)

    # Действия без требования первичного ключа
    if   key == 'new' and dict_form_object:
        data = model_bwp.object_new(dict_form_object, post, user)

    # Проверка на присутствие первичного ключа для дальнейших обработчиков
    elif key not in actions_with_pk or not pk:
        return JSONResponse(status=400)

    # Далее действия только с обозначенным первичным ключом
    elif key == 'upd' and dict_form_object:
        data = model_bwp.object_upd(pk, dict_form_object, post, user)
    elif key == 'upd' and array_form_compose:
        data = model_bwp.compose_upd(pk, array_form_compose, post, user)
    elif key == 'del':
        data = model_bwp.object_del(pk, user)
    elif key == 'get':
        data = model_bwp.object_get(pk, user)
    else:
        return JSONResponse(status=400)

    return JSONResponse(data=data)

QUICKAPI_DEFINED_METHODS = {
    'get_settings': 'bwp.views.API_get_settings',
    'object_action': 'bwp.views.API_object_action',
}

@csrf_exempt
def api(request):
    return _api(request, QUICKAPI_DEFINED_METHODS)

########################################################################
#                             END API                                  #
########################################################################
