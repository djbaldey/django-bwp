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
from django.http import HttpResponseBadRequest, HttpResponseForbidden
#~ from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login as _login, logout as _logout
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.forms.models import modelform_factory

from quickapi.http import JSONResponse, JSONRedirect, MESSAGES, DjangoJSONEncoder
from quickapi.views import switch_language, index as quickapi_index, get_methods
from quickapi.decorators import login_required, api_required

from bwp.sites import site
from bwp.models import TempUploadFile
from bwp.forms import BWPAuthenticationForm, TempUploadFileForm
from bwp import conf
from bwp.conf import settings
from bwp.utils import print_debug
from bwp.utils.http import get_http_400, get_http_403, get_http_404

from bwp.contrib.reports.models import Document as Report

import datetime, os

########################################################################
#                               PAGES                                  #
########################################################################
@never_cache
def index(request, extra_context={}):
    """
    Displays the main bwp index page, which lists all of the installed
    apps that have been registered in this site.
    """
    switch_language(request)
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
    switch_language(request)
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
    switch_language(request)
    defaults = {
        'extra_context': extra_context,
        'template_name': 'bwp/logout.html',
    }
    return _logout(request, **defaults)

@csrf_exempt
def upload(request, model, **kwargs):
    """ Загрузка файла во временное хранилище для определённого поля
        объекта.

        Формат ключа "data" в ответе:
        {
            'id'  : 'идентификатор загруженного файла',
            'name': 'имя файла',
        }
    """
    switch_language(request)
    user = request.user

    if not user.is_authenticated() and not conf.BWP_TMP_UPLOAD_ANONYMOUS:
        return redirect('bwp.views.login')

    # Получаем модель BWP со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)
    perms = model_bwp.get_model_perms(request)

    if not model_bwp or not (perms['add'] or perms['change']):
        print_debug("not model_bwp or not (perms['add'] or perms['change'])")
        return HttpResponseForbidden(MESSAGES[403])

    # Только метод POST
    if request.method != 'POST':
        print_debug("request.method != 'POST'")
        return HttpResponseBadRequest(MESSAGES[400])
    else:
        print_debug(request.POST, request.FILES)
        form = TempUploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return JSONResponse(data=obj.pk)
        else:
            print_debug("not form.is_valid()")
            return HttpResponseBadRequest(MESSAGES[400])
    return JSONResponse(data=None)

########################################################################
#                             END PAGES                                #
########################################################################
def get_form_instance(request, bwp_model, data=None, files={}, instance=None):
    """
    Возвращает экземпляр формы, которая используются для добавления
    или редактирования объекта.

    Аргумент `instance` является экземпляром модели `model_name`
    (принимается только если эта форма будет использоваться для
    редактирования существующего объекта).
    
    files = {'field': ('фото.jpg', 'path/in/bwp_tmp_upload/фото.jpg'}
    """
    model = bwp_model.model
    defaults = {}
    if bwp_model.form:
        defaults['form'] = bwp_model.form
    if bwp_model.fields:
        defaults['fields'] = bwp_model.fields

    print_debug('defaults:', defaults, '\ndata:', data, '\nfiles:', files)
    return modelform_factory(model, **defaults)(data=data, files=files, instance=instance)

def get_instance(request, pk, model_name):
    """ Возвращает зкземпляр указаной модели """
    model = site.model_dict(request).get(model_name)
    return model.objects.get(pk=pk)

def set_file_fields(bwp_model, instance, data):
    """ Устанавливает файловые поля и возвращает зкземпляр указаной
        модели без сохранения
    """
    for field in bwp_model.get_file_fields():
        temp_id = data.get(field, None)
        if temp_id in (0, ''):
            real_field = getattr(instance, field)
            real_field.delete(save=False)
        elif not temp_id is None:
            try:
                upl = TempUploadFile.objects.get(pk=temp_id) 
            except Exception as e:
                print e
                continue
            else:
                real_field = getattr(instance, field)
                real_field.save(upl.file.name, upl.file.file, save=False)

    return instance

def set_user_field(model_bwp, instance, user, save=False):
    """ Устанавливает пользователя, изменившего объект """
    if model_bwp.user_field:
        setattr(instance, model_bwp.user_field, user)
    if save:
        instance.save()
    return instance

class MethodError(Exception):
    message = _('Error in parameters for the method')

class PermissionError(Exception):
    message = _('Access denied')

def _get_app(request, app):
    """ Выполняет проверку прав и возвращает приложение """

    if site.has_permission(request):
        app = site.apps[app]
        if app.has_permission(request):
            return app
    raise PermissionError()

def _get_model(request, app, model):
    """ Выполняет проверку любых прав CRUD и возвращает модель """

    app = _get_app(request, app)
    model = app.models[model]
    if   model.has_read_permission(request):
        return model
    elif model.has_create_permission(request):
        return model
    elif model.has_update_permission(request):
        return model
    elif model.has_delete_permission(request):
        return model
    raise PermissionError()

########################################################################
#                               API                                    #
########################################################################

@api_required
@login_required
def API_get_scheme(request, **kwargs):
    """ *Возвращает схему приложения, сформированную для конкретного
        пользователя.*
        
        ##### ЗАПРОС
        Без параметров.
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `
        - возвращается словарь схемы сервиса.
        `
    """
    if not site.has_permission(request):
        return JSONResponse(message=403)
    data = site.get_scheme(request)
    return JSONResponse(data=data)

@api_required
@login_required
def API_get_objects(request, app, model, pk=None, foreign=None, compose=None, 
    page=1, per_page=None, query=None, ordering=None, fields_search=None, filters=None, **kwargs):
    """ *Возвращает список объектов.*
        Если не указан объект, то возвращает список объектов модели.
        Иначе возвращает связанные объекты композиции или
        поля для указанного, конкретного объекта.

        ##### ЗАПРОС
        Параметры:

        1. **"app"**        - название приложения, например: "users";
        2. **"model"**      - название модели приложения, например: "user";
        3. **"pk"**         - ключ объекта модели, по-умолчанию == None;
        4. **"foreign"**    - поле объекта с внешним ключом (fk, m2m, o2o),
                            объекты которого должны быть возвращены,
                            по-умолчанию == None;
        5. **"compose"**    - уникальное название класса модели Compose, 
                            объекты которой должны быть возвращены,
                            по-умолчанию == None;

        6. **"page"**       - номер страницы, по-умолчанию == 1;
        7. **"per_page"**   - количество на странице, по-умолчанию определяется моделью;
        8. **"query"**      - поисковый запрос, если есть;
        9. **"ordering"**   - сортировка объектов, если отлична от умолчания;
        10. **"fields_search"** - поля объектов для поиска, если отлично от умолчания;
        11. **"filters"** - дополнительные фильтры, если есть;

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

    model = _get_model(request, app, model)
    # запрещено обновлять объект
    if pk and not model.has_update_permission(request):
        raise PermissionError()

    options = {
        'request': request,
        'page': page,
        'per_page': per_page,
        'query': query,
        'ordering': ordering,
        'fields_search': fields_search,
        'filters': filters,
    }

    if pk:
        # Возвращаем объекты композиции, если указано
        if compose:
            object = model.get(pk=pk)
            options['object'] = object
            compose = model.composes[compose]
            return compose.filter(**options)

        # Возвращаем объекты внешних связей, если указано
        elif foreign:
            field, raw_model, direct, m2m = model.opts.get_field_by_name(foreign)
            rel_app = site.apps.get(raw_model._meta.app_label)
            rel_model = rel_app.models.get(raw_model.__class__.__name__.lower())
            return rel_model.filter(**options)

        else:
            raise MethodError()

    # Возвращаем объекты модели
    return model.filter(**options)









@api_required
@login_required
def API_get_object(request, model, pk=None, copy=None, clone=None, filler={}, **kwargs):
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
        5. **"filler"** - словарь полей для заполнения нового объекта.

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
        print_debug(kwargs)
        fil = {}
        fields = model_bwp.get_fields()
        fil = dict([(key, val) for key, val in filler.items() \
                                            if key in fields])
        return model_bwp.new(request, filler=fil)
    else:
        if copy or clone:
            # Копия
            return model_bwp.copy(request, pk, clone)
        # Существующий
        return model_bwp.get(request, pk)



@api_required
@login_required
def API_m2m_commit(request, model, pk, compose, action, objects, **kwargs):
    """ *Добавление или удаление объектов в M2M полях.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"model"** - модель объекта, которому принадлежит поле;
        2. **"pk"**    - ключ объекта, которому принадлежит поле;
        3. **"compose"** - композиция(поле);
        4. **"action"** - действие, которое необходимо выполнить;
        5. **"objects"** - список идентификаторов объектов;
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        `Boolean`
    """
    if not objects:
        return JSONResponse(data=False, status=400, message=unicode(_("List objects is blank!")))

    # Получаем модель BWP и композиции со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)
    compose = model_bwp.compose_dict(request).get(compose)
    objects = compose.queryset().filter(pk__in=objects)
    try:
        object = compose.related_model.queryset(request, **kwargs).get(pk=pk)
    except:
        return get_http_404(request)
    else:
        if action in ('add', 'create') and compose.has_create_permission(request):
            result = compose.add_objects_in_m2m(object, objects)
        elif action == 'delete' and compose.has_delete_permission(request):
            result = compose.delete_objects_in_m2m(object, objects)
        else:
            result = False
        if not result:
            return JSONResponse(data=False, status=400)

        set_user_field(model_bwp, object, request.user, save=True)

    return JSONResponse(data=True, message=unicode(_("Commited!")))

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
    transaction.commit()
    if not objects:
        transaction.rollback()
        return JSONResponse(data=False, status=400, message=unicode(_("List objects is blank!")))
    model_name = model_bwp = None
    try:
        for item in objects:
            # Уменьшение ссылок на объекты, если они существуют
            # в прошлой ротации
            if model_name != item['model']:
                model_name = item['model']
                model_bwp = site.bwp_dict(request).get(model_name)
            action = item['action'] # raise AttributeError()
            for name, val in item['fields'].items():
                field = model_bwp.opts.get_field_by_name(name)[0]
                if field.rel and isinstance(val, list) and len(val) == 2:
                    item['fields'][name] = val[0]
                elif isinstance(field, models.DateTimeField) and val:
                    item['fields'][name] = val.replace('T', ' ')
            data = item['fields']
            # Новый объект
            if not item.get('pk', False):
                if model_bwp.has_create_permission(request):
                    instance = model_bwp.model()
                    instance = set_file_fields(model_bwp, instance, data)
                    instance = set_user_field(model_bwp, instance, request.user)
                    form = get_form_instance(request, model_bwp, data=data, instance=instance)
                    if form.is_valid():
                        object = form.save()
                        model_bwp.log_addition(request, object)
                    else:
                        transaction.rollback()
                        return JSONResponse(status=400, message=unicode(form.errors))
            # Удаляемый объект
            elif action == 'delete':
                instance = get_instance(request, item['pk'], item['model'])
                if model_bwp.has_delete_permission(request, instance):
                    model_bwp.log_deletion(request, instance, unicode(instance))
                    instance.delete()
            # Обновляемый объект
            elif action in ('change', 'update'): # raise AttributeError()
                instance = get_instance(request, item['pk'], item['model'])
                instance = set_user_field(model_bwp, instance, request.user)
                if model_bwp.has_update_permission(request, instance):
                    instance = set_file_fields(model_bwp, instance, data)
                    form = get_form_instance(request, model_bwp, data=data, instance=instance)
                    if form.is_valid():
                        object = form.save()
                        fix = item.get('fix', {})
                        model_bwp.log_change(request, object, ', '.join(fix.keys()))
                    else:
                        transaction.rollback()
                        return JSONResponse(status=400, message=unicode(form.errors))

    except Exception as e:
        transaction.rollback()
        print_debug('def API_commit.objects ==', objects)
        if settings.DEBUG:
            return JSONResponse(status=500, message=unicode(e))
        raise e
    else:
        transaction.commit()
    return JSONResponse(data=True, message=unicode(_("Commited!")))

@api_required
@login_required
def API_device_list(request, **kwargs):
    """ *Получение списка доступных устройств.*
        
        ##### ЗАПРОС
        Без параметров.
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        список устройств
    """
    data = []
    if site.devices:
        data = site.devices.get_list()
    return JSONResponse(data=data)

@api_required
@login_required
def API_device_command(request, device, command, params={}, **kwargs):
    """ *Выполнение команды на устройстве.*
        
        ##### ЗАПРОС
        Параметры:
        
        1. **"device"** - идентификатор устройства;
        2. **"command"** - команда(метод) устройства;
        3. **"params"** - параметры к команде (по-умолчанию == {});
        
        ##### ОТВЕТ
        Формат ключа **"data"**:
        результат выполнения команды
    """
    # Получение устройства согласно привилегий
    device = site.devices.get_devices(request).get(device)
    if device.device:
        try:
            attr = getattr(device.device, command)
            data = attr(**params)
            return JSONResponse(data=data)
        except Exception as e:
            print e
            try:
                message = unicode(e)
            except UnicodeError:
                message = str(e)
            return JSONResponse(status=400, message=message)
    return JSONResponse(status=400)

@api_required
@login_required
def API_get_collection_report_url(request, model, report,
    query=None, order_by=None, fields=None, filters=None, **kwargs):
    """ *Формирование отчёта для коллекции.*

        ##### ЗАПРОС
        Параметры:

        1. **"model"** - уникальное название модели, например: "auth.user";
        2. **"report"** - ключ отчёта;
        3. **"query"** - поисковый запрос;
        4. **"order_by"** - сортировка объектов.
        5. **"fields"** - поля объектов для поиска.
        6. **"filters"** - дополнительные фильтры.

        ##### ОТВЕТ
        ссылка на файл сформированного отчёта
    """
    # Получаем модель BWP со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)
    report = Report.objects.get(pk=report)

    options = {
        'request': request,
        'query': query,
        'order_by': order_by,
        'fields': fields,
        'filters': filters,
    }

    qs = model_bwp.filter_queryset(**options)
    
    filters = filters or []

    ctx = {'data': qs, 'filters': [ x for x in filters if x['active']]}
    url = report.render_to_media_url(context=ctx, user=request.user)
    return JSONResponse(data=url)

@api_required
@login_required
def API_get_object_report_url(request, model, pk, report, **kwargs):
    """ *Формирование отчёта для объекта.*

        ##### ЗАПРОС
        Параметры:

        1. **"model"** - уникальное название модели, например: "auth.user";
        2. **"pk"** - ключ объекта;
        3. **"report"** - ключ отчёта;

        ##### ОТВЕТ
        ссылка на файл сформированного отчёта
    """
    # Получаем модель BWP со стандартной проверкой прав
    model_bwp = site.bwp_dict(request).get(model)
    report = Report.objects.get(pk=report)

    if pk is None:
        return HttpResponseBadRequest()

    options = {
        'request': request,
        'pk': pk,
        'as_lookup': True,
    }

    obj = model_bwp.queryset(request, **kwargs).get(pk=pk)

    ctx = {'data': obj}
    url = report.render_to_media_url(context=ctx, user=request.user)
    return JSONResponse(data=url)

dict_methods = {
    'get_scheme':       'bwp.views.API_get_scheme',
    'get_object':       'bwp.views.API_get_object',
    'get_collection':   'bwp.views.API_get_collection',
    'm2m_commit':       'bwp.views.API_m2m_commit',
    'commit':           'bwp.views.API_commit',
    'get_collection_report_url': 'bwp.views.API_get_collection_report_url',
    'get_object_report_url': 'bwp.views.API_get_object_report_url',
}

if site.devices:
    dict_methods['device_list']    = 'bwp.views.API_device_list'
    dict_methods['device_command'] = 'bwp.views.API_device_command'

METHODS = get_methods(dict_methods)

@csrf_exempt
def api(request):
    return quickapi_index(request, methods=METHODS)

########################################################################
#                             END API                                  #
########################################################################
