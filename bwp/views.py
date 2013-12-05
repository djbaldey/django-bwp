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
from django.db import transaction, models, router
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
                    'pk': 1,
                    '__unicode__': 'Первый',
                    'first_name': u'First',
                    ...
                },
                {
                    'pk': 2,
                    '__unicode__': 'Второй',
                    'first_name': u'Second',
                    ...
                }
            ],
            'previous_page_number': 0,
            'start_index': 1
        }`
    """

    model = _get_model(request, app, model)

    # Если запрещено обновлять объект, то поля внешних связей должны
    # быть нередактируемые, соотвественно, такого сочетания входных
    # параметров просто не должно быть в принципе.
    # Поэтому это - "проверка на дурака".
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
            object = model.get_object(pk=pk)
            options['object'] = object
            compose = model.composes[compose]
            objects = compose.serialize_queryset(**options)

        # Возвращаем объекты внешних связей, если указано
        elif foreign:
            field, _null, direct, m2m = model.opts.get_field_by_name(foreign)
            rel_app = site.apps.get(field.model._meta.app_label)
            rel_model = rel_app.models.get(field.model.__class__.__name__.lower())
            options['limit_choices_to'] = field.rel.limit_choices_to
            options['columns'] = ['__unicode__']
            objects = rel_model.serialize_queryset(**options)

        else:
            raise MethodError()

    else:
        # Возвращаем объекты модели
        objects = model.serialize_queryset(**options)

    return JSONResponse(data=objects)

@api_required
@login_required
def API_get_summary(request, app, model, pk=None, compose=None, 
    query=None, ordering=None, fields_search=None, filters=None, **kwargs):
    """ *Возвращает итоговые данные по набору данных.*
        Если не указан объект, то возвращает для объектов модели.
        Иначе возвращает для композиции объекта.

        ##### ЗАПРОС
        Параметры:

        1. **"app"**        - название приложения, например: "users";
        2. **"model"**      - название модели приложения, например: "user";
        3. **"pk"**         - ключ объекта модели, по-умолчанию == None;
        4. **"compose"**    - уникальное название класса модели Compose, 
                            объекты которой должны быть возвращены,
                            по-умолчанию == None;
        5. **"query"**      - поисковый запрос, если есть;
        6. **"ordering"**   - сортировка объектов, если отлична от умолчания;
        7. **"fields_search"** - поля объектов для поиска, если отлично от умолчания;
        8. **"filters"** - дополнительные фильтры, если есть;

        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            'total_sum': 2000.00,
            'total_avg': 200.00,
            'discount_sum': 100.00,
            'discount_avg': 10.00,
        }`
    """

    model = _get_model(request, app, model)

    options = {
        'request': request,
        'query': query,
        'ordering': ordering,
        'fields_search': fields_search,
        'filters': filters,
    }

    if pk:
        # Возвращаем итоги композиции, если указано
        if compose:
            object = model.get_object(pk=pk)
            options['object'] = object
            compose = model.composes[compose]
            summary = compose.get_summary(**options)

        else:
            raise MethodError()

    else:
        # Возвращаем итоги модели
        summary = model.get_summary(**options)

    return JSONResponse(data=summary)

@api_required
@login_required
def API_read_object(request, app, model, pk, **kwargs):
    """ *Считывает из базы данных и возвращает объект.*

        ##### ЗАПРОС
        Параметры:
        
        1. **"app"**    - название приложения, например: "users";
        2. **"model"**  - название модели приложения, например: "user";
        3. **"pk"**     - ключ объекта модели;

        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            объект
        }`
    """

    model = _get_model(request, app, model)

    # Если запрещено считывать объект, то и на клиенте не должен
    # вызываться данный метод.
    # Поэтому это - "проверка на дурака".
    if not model.has_read_permission(request):
        raise PermissionError()

    object = model.get_object(pk=pk)

    return JSONResponse(data=model.serialize(object))

@api_required
@login_required
def API_create_object(request, app, model, fields, **kwargs):
    """ *Создание объекта.*

        ##### ЗАПРОС
        Параметры:

        1. **"app"**    - название приложения, например: "users";
        2. **"model"**  - название модели приложения, например: "user";
        4. **"fields"** - словарь полей для заполнения;

        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            объект
        }`
    """

    model = _get_model(request, app, model)

    # Если запрещено создавать объект, то и на клиенте не должен
    # вызываться данный метод.
    # Поэтому это - "проверка на дурака".
    if not model.has_create_permission(request):
        raise PermissionError()

    # сразу же должны установиться поля пользователя,
    # если в модели такие есть
    object = model.model()

    TMP = []    # список временных файлов, подлежащих удалению
                # после сохранения объекта
    M2M = []    # отложенная запись m2m полей

    editable_fields = set(model.editable_fields).intersection(fields.keys())
    for fname in editable_fields:
        field, _null, direct, m2m = model.opts.get_field_by_name(fname)
        value = fields[fname]
        attr = getattr(object, fname)

        # Поля с внешними связями
        if hasattr(field, 'rel'):
            using = router.db_for_write(field.model)
            full_manager = field.rel.to._default_manager.using(using)
            manager = full_manager.complex_filter(field.rel.limit_choices_to)
            if m2m:
                objects = manager.filter(pk__in=value)
                M2M.append((attr, objects))
            elif value:
                attr = manager.get(pk=value)

        # Файловые поля с идентификаторами предварительно
        # загруженных файлов
        elif fname in model.fields_file and value:
            tmp = TempUploadFile.objects.get(pk=value)
            attr.save(tmp.file.name, tmp.file.file, save=False)
            TMP.append(tmp)

        # Обычные поля
        else:
            attr = v

    object = model.set_user_field(object, request.user)
    try:
        object.save()
    except Exception as e:
        return JSONResponse(status=400, message=unicode(e))

    for t in TMP:
        t.delete()

    return JSONResponse(data=model.serialize(object))

@api_required
@login_required
def API_update_object(request, app, model, pk, fields, **kwargs):
    """ *Обновление полей объекта.*

        ##### ЗАПРОС
        Параметры:

        1. **"app"**    - название приложения, например: "users";
        2. **"model"**  - название модели приложения, например: "user";
        3. **"pk"**     - ключ объекта модели;
        4. **"fields"** - словарь полей для изменения;

        ##### ОТВЕТ
        Формат ключа **"data"**:
        `{
            объект
        }`
    """

    if not fields:
        return JSONResponse(data=False, status=400,
                            message=_("List fileds is blank!"))

    model = _get_model(request, app, model)

    # Если запрещено обновлять объект, то и на клиенте не должен
    # вызываться данный метод.
    # Поэтому это - "проверка на дурака".
    if not model.has_update_permission(request):
        raise PermissionError()

    # сразу же должны установиться поля пользователя,
    # если в модели такие есть
    object = model.get_object(pk=pk, user=request.user)

    TMP = []    # список временных файлов, подлежащих удалению
                # после сохранения объекта

    editable_fields = set(model.editable_fields).intersection(fields.keys())
    for fname in editable_fields:
        field, _null, direct, m2m = model.opts.get_field_by_name(fname)
        value = fields[fname]
        attr = getattr(object, fname)

        # Поля с внешними связями
        if hasattr(field, 'rel'):
            using = router.db_for_write(field.model)
            full_manager = field.rel.to._default_manager.using(using)
            manager = full_manager.complex_filter(field.rel.limit_choices_to)
            if m2m:
                _value = set(attr.values_list('pk', flat=True))
                objects = full_manager.filter(pk__in=_value.difference(value))
                attr.remove(*objects)

                objects = manager.filter(pk__in=value)
                attr.add(*objects)
            else:
                if value:
                    attr = manager.get(pk=value)
                else:
                    attr = None

        # Файловые поля с идентификаторами предварительно
        # загруженных файлов
        elif fname in model.fields_file:
            if not value:
                attr.delete(save=False)
            else:
                tmp = TempUploadFile.objects.get(pk=value)
                attr.save(tmp.file.name, tmp.file.file, save=False)
                TMP.append(tmp)

        # Обычные поля
        else:
            attr = v

    try:
        object.save()
    except Exception as e:
        return JSONResponse(status=400, message=unicode(e))

    for t in TMP:
        t.delete()

    return JSONResponse(data=model.serialize(object))

@api_required
@login_required
def API_delete_object(request, app, model, pk, confirm=False, **kwargs):
    """ *Удаление объекта.*

        ##### ЗАПРОС
        Параметры:

        1. **"app"**    - название приложения, например: "users";
        2. **"model"**  - название модели приложения, например: "user";
        3. **"pk"**     - ключ объекта модели;
        4. **"confirm"** - флаг подтверждения удаления;

        ##### ОТВЕТ
        Формат ключа **"data"**, если подтверждено:
        `Boolean`

        Если не подтверждено, то передаётся список зависимых объектов,
        которые будут удалены вместе с этим объектом.

    """

    model = _get_model(request, app, model)

    # Если запрещено удалять объект, то и на клиенте не должен
    # вызываться данный метод.
    # Поэтому это - "проверка на дурака".
    if not model.has_delete_permission(request):
        raise PermissionError()

    using = router.db_for_write(model.model)
    manager = model.model._default_manager.usung(using)

    object = manager.get(pk=pk)

    # TODO: реализовать удаление и возврат списка удаляемых объектов

    if confirm:
        try:
            object.delete()
        except Exception as e:
            return JSONResponse(status=400, message=unicode(e))
        else:
            return JSONResponse(data=True)
    else:
        roots = []
        #~ related_objects = model.opts.get_all_related_objects()

        return JSONResponse(data=roots)

@api_required
@login_required
def API_action(request, app, model, action, list_pk, confirm=False, **kwargs):
    """ *Действие со списком объектов.*
        
        ##### ЗАПРОС
        1. **"app"**     - название приложения, например: "users";
        2. **"model"**   - название модели приложения, например: "user";
        3. **"action"**  - действие, например: "delete";
        4. **"list_pk"** - список ключей объекта модели;
        5. **"confirm"**  - флаг подтверждения действия, если нужен;
        
        ##### ОТВЕТ
        Формат ключа **"data"**, если подтверждено:
        `Boolean`

        Если не подтверждено и если требуется подтверждение,
        то передаётся иерархический список объектов,
        и сообщение подтверждения, например:
        `{
        'message': 'Все объекты будут удалены. Вы дествительно желаете сделать это?',
        'objects': [
            <object1>,
            [<object2>, [<nested_2.1>, <nested_2.2>]],
            [<object3>, [
                [<nested_3.1>, [<nested_3.1.1>, <nested_3.1.2>]],
                [<nested_3.2>, [<nested_3.2.1>, <nested_3.2.2>]],
                ...
            ]],
        }`
    """

    model = _get_model(request, app, model)

    using = router.db_for_write(model.model)
    manager = model.model._default_manager.usung(using)

    objects = manager.filter(pk__in=list_pk)

    # TODO: реализовать действия и возврат списка удаляемых объектов

    if confirm:
        try:
            model.action(action, objects)
        except Exception as e:
            return JSONResponse(status=400, message=unicode(e))
        else:
            return JSONResponse(data=True)
    else:
        roots = []
        #~ related_objects = model.opts.get_all_related_objects()

        return JSONResponse(data=roots)


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
            print 'API_device_command', e
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
    'get_scheme':    'bwp.views.API_get_scheme',
    'get_objects':   'bwp.views.API_get_objects',
    'read_object':   'bwp.views.API_read_object',
    'create_object': 'bwp.views.API_create_object',
    'update_object': 'bwp.views.API_update_object',
    'delete_object': 'bwp.views.API_delete_object',
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
