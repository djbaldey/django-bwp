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
from quickapi.views import index as quickapi_index, get_methods
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
    ctx = {'DEBUG': settings.DEBUG, 'title': _('bwp')}
    user = request.user
    if not user.is_authenticated():
        return redirect('bwp:login')
    ctx.update(extra_context)
    return render_to_response('bwp/index.html', ctx,
                            context_instance=RequestContext(request,))

@never_cache
def login(request, extra_context={}):
    """ Displays the login form for the given HttpRequest. """
    context = {
        'title': _('Log in'),
        'app_path': request.get_full_path(),
        REDIRECT_FIELD_NAME: redirect('bwp:index').get('Location', '/'),
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
    user = request.user

    if not user.is_authenticated() and not conf.BWP_TMP_UPLOAD_ANONYMOUS:
        return redirect('bwp:login')

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
def API_bwp_scheme(request, **kwargs):
    """ 
    Возвращает схему приложения, сформированную для конкретного
    пользователя.
    """
    if not site.has_permission(request):
        return JSONResponse(message=403)
    data = site.get_scheme(request)
    return JSONResponse(data=data)

API_bwp_scheme.__doc__ = _("""
*Returns the application schema formed for a specific user.*

#### Request parameters
Nothing

#### Returned object
Object (dict) of scheme

""")


@api_required
@login_required
def API_model_objects(request, app, model, pk=None, foreign=None, component=None, 
    page=1, per_page=None, query=None, ordering=None, fields_search=None, filters=None, **kwargs):
    """ 
    Возвращает список объектов.
    Если не указан объект, то возвращает список объектов модели.
    Иначе возвращает связанные объекты композиции или поля для
    указанного, конкретного объекта.
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
        # Возвращаем компоненты, если указано
        if component:
            component_bwp = model.components_dict[component]
            if not component_bwp.has_permission(request):
                raise PermissionError()
            obj = model.get_object(pk=pk)
            rel = getattr(obj, component)
            options['queryset'] = rel.select_related()
            objects = component_bwp.serialize_queryset(**options)

        # Возвращаем объекты внешних связей, если указано
        elif foreign:
            field, _null, direct, m2m = model.opts.get_field_by_name(foreign)
            rel_app = site.apps.get(field.model._meta.app_label)
            rel_model = rel_app.models.get(field.opts.concrete_model.__name__.lower())
            options['limit_choices_to'] = field.rel.limit_choices_to
            options['columns'] = ['__unicode__']
            objects = rel_model.serialize_queryset(**options)

        else:
            raise MethodError()

    else:
        # Возвращаем объекты модели
        objects = model.serialize_queryset(**options)

    return JSONResponse(data=objects)

API_model_objects.__doc__ = _("""
*Returns a list of objects.*

If the object is not specified, returns a list of model objects.
Otherwise returns related objects composition or field for a specified,
a specific object.

#### Request parameters

1. **"app"**        - name of the application, for example: "users";
2. **"model"**      - model name of the application, for example: "user";
3. **"pk"**         - the key of the object model, the default == None;
4. **"foreign"**    - object field with a foreign key (fk, m2m, o2o)
                      whose objects must be returned, the default == None;
5. **"component"**  - name relationship to the model ComponentBWP,
                      objects which must be returned,
                      by default == None;

6. **"page"**       - page number, the default == 1;
7. **"per_page"**   - the number on the page, the default determined by
                      the model;
8. **"query"**      - search query, if there is;
9. **"ordering"**   - sorting objects, if different from the default;
10. **"fields_search"** - field objects to find, if different from the
                          default;
11. **"filters"**       - additional filters if there are;

#### Returned object
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
            '__unicode__': 'First object',
            'first_name': 'First',
            ...
        },
        {
            'pk': 2,
            '__unicode__': 'Second object',
            'first_name': 'Second',
            ...
        }
    ],
    'previous_page_number': 0,
    'start_index': 1
}`

""")


@api_required
@login_required
def API_model_summary(request, app, model, pk=None, component=None, 
    query=None, ordering=None, fields_search=None, filters=None, **kwargs):
    """
    Возвращает итоговые данные по набору данных.
    Если не указан объект, то возвращает для объектов модели.
    Иначе возвращает для композиции объекта.
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
        # Возвращаем итоги компонентов, если указано
        if component:
            component_bwp = model.components_dict[component]
            if not component_bwp.has_permission(request):
                raise PermissionError()
            obj = model.get_object(pk=pk)
            rel = getattr(obj, component)
            options['queryset'] = rel.select_related()
            summary = component_bwp.get_summary(**options)

        else:
            raise MethodError()

    else:
        # Возвращаем итоги модели
        summary = model.get_summary(**options)

    return JSONResponse(data=summary)

API_model_summary.__doc__ = _("""
*Returns a summary of the data set.*

If the object is not specified, it returns the object model.
Otherwise returns for the composition of the object.

#### Request parameters

1. **"app"**        - name of the application, for example: "users";
2. **"model"**      - model name of the application, for example: "user";
3. **"pk"**         - the key of the object model, the default == None;
4. **"component"**  - name relationship to the model ComponentBWP,
                      objects which must be returned,
                      by default == None;
5. **"query"**      - search query, if there is;
6. **"ordering"**   - sorting objects, if different from the default;
7. **"fields_search"** - field objects to find, if different from the
                         default;
8. **"filters"**       - additional filters if there are;

#### Returned object
`{
    'total_sum': 2000.00,
    'total_avg': 200.00,
    'discount_sum': 100.00,
    'discount_avg': 10.00,
}`

""")


@api_required
@login_required
def API_model_action(request, app, model, action, list_pk, confirm=False, **kwargs):
    """
    Действие со списком объектов.
    Если не подтверждено и если требуется подтверждение,
    то передаётся иерархический список объектов,
    и сообщение подтверждения
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

API_model_action.__doc__ = _("""
*Action for the list of objects.*

#### Request parameters

1. **"app"**     - name of the application, for example: "users";
2. **"model"**   - model name of the application, for example: "user";
3. **"action"**  - action, example: "delete";
4. **"list_pk"** - list object keys of model;
5. **"confirm"** - flag confirm, if need;

#### Returned object

If confirmed, or the confirmation is not required:
`Boolean`

If not confirmed, and if confirmation is required, then transferred to
the hierarchical list of objects and a confirmation message, example:

`{
'message': 'All the objects will be deleted. You really want to do this?',
'objects': [
    <object1>,
    [<object2>, [<nested_2.1>, <nested_2.2>]],
    [<object3>, [
        [<nested_3.1>, [<nested_3.1.1>, <nested_3.1.2>]],
        [<nested_3.2>, [<nested_3.2.1>, <nested_3.2.2>]],
        ...
    ]],
}`

""")


@api_required
@login_required
def API_object_read(request, app, model, pk, **kwargs):
    """
    Считывает из базы данных и возвращает объект.
    """

    model = _get_model(request, app, model)

    # Если запрещено считывать объект, то и на клиенте не должен
    # вызываться данный метод.
    # Поэтому это - "проверка на дурака".
    if not model.has_read_permission(request):
        raise PermissionError()

    obj = model.get_object(pk=pk)

    return JSONResponse(data=model.serialize(obj)[0])

API_object_read.__doc__ = _("""
*Reads from the database and returns an object.*

#### Request parameters

1. **"app"**    - name of the application, for example: "users";
2. **"model"**  - model name of the application, for example: "user";
3. **"pk"**     - the key of the object model;

#### Returned object
`{ object }`

""")


@api_required
@login_required
def API_object_create(request, app, model, fields, **kwargs):
    """
    Создание объекта
    """

    model = _get_model(request, app, model)

    # Если запрещено создавать объект, то и на клиенте не должен
    # вызываться данный метод.
    # Поэтому это - "проверка на дурака".
    if not model.has_create_permission(request):
        raise PermissionError()

    # сразу же должны установиться поля пользователя,
    # если в модели такие есть
    obj = model.model()

    TMP = []    # список временных файлов, подлежащих удалению
                # после сохранения объекта
    M2M = []    # отложенная запись m2m полей

    editable_fields = set(model.editable_fields).intersection(fields.keys())
    for fname in editable_fields:
        field, _null, direct, m2m = model.opts.get_field_by_name(fname)
        value = fields[fname]

        attr = getattr(obj, fname)
        rel  = getattr(field, 'rel', None)

        # Поля с внешними связями
        if rel:
            using = router.db_for_write(field.model)
            full_manager = rel.to._default_manager.using(using)
            manager = full_manager.complex_filter(field.rel.limit_choices_to)
            if m2m:
                objects = manager.filter(pk__in=value)
                M2M.append((attr, objects))
            elif value:
                setattr(obj, fname, manager.get(pk=value))

        # Файловые поля с идентификаторами предварительно
        # загруженных файлов
        elif fname in model.fields_file and value:
            tmp = TempUploadFile.objects.get(pk=value)
            attr.save(tmp.file.name, tmp.file.file, save=False)
            TMP.append(tmp)

        # Обычные поля
        else:
            setattr(obj, fname, value)

    obj = model.set_user_field(obj, request.user)
    try:
        obj.save()
    except Exception as e:
        return JSONResponse(status=400, message=unicode(e))

    for t in TMP:
        t.delete()

    return JSONResponse(data=model.serialize(obj)[0])

API_object_create.__doc__ = _("""
*Object creation.*

#### Request parameters

1. **"app"**    - name of the application, for example: "users";
2. **"model"**  - model name of the application, for example: "user";
3. **"fields"** - dictionary fields;

#### Returned object
`{ object }`

""")


@api_required
@login_required
def API_object_update(request, app, model, pk, fields, **kwargs):
    """
    Обновление полей объекта
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
    obj = model.get_object(pk=pk, user=request.user)

    TMP = []    # список временных файлов, подлежащих удалению
                # после сохранения объекта

    editable_fields = set(model.editable_fields).intersection(fields.keys())
    for fname in editable_fields:
        field, _null, direct, m2m = model.opts.get_field_by_name(fname)
        value = fields[fname]

        attr = getattr(obj, fname)
        rel = getattr(field, 'rel', None)

        # Поля с внешними связями
        if rel:
            using = router.db_for_write(field.model)
            full_manager = rel.to._default_manager.using(using)
            manager = full_manager.complex_filter(field.rel.limit_choices_to)
            if m2m:
                _value = set(attr.values_list('pk', flat=True))
                objects = full_manager.filter(pk__in=_value.difference(value))
                attr.remove(*objects)

                objects = manager.filter(pk__in=value)
                attr.add(*objects)
            else:
                if value:
                    setattr(obj, fname, manager.get(pk=value))
                else:
                    setattr(obj, fname, None)

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
            setattr(obj, fname, value)

    try:
        obj.save()
    except Exception as e:
        return JSONResponse(status=400, message=unicode(e))

    for t in TMP:
        t.delete()

    return JSONResponse(data=model.serialize(obj)[0])

API_object_update.__doc__ = _("""
*Update the object's fields.*

#### Request parameters

1. **"app"**    - name of the application, for example: "users";
2. **"model"**  - model name of the application, for example: "user";
3. **"pk"**     - the key of the object model;
3. **"fields"** - dictionary fields for update;

#### Returned object
`{ object }`

""")


@api_required
@login_required
def API_object_delete(request, app, model, pk, confirm=False, **kwargs):
    """
    Удаление объекта.
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
    manager = model.model._default_manager.using(using)

    obj = manager.get(pk=pk)

    # TODO: реализовать удаление и возврат списка удаляемых объектов

    if confirm:
        try:
            obj.delete()
        except Exception as e:
            return JSONResponse(status=400, message=unicode(e))
        else:
            return JSONResponse(data=True)
    else:
        roots = []
        print model.opts.get_all_related_objects()
        #~ related_objects = model.opts.get_all_related_objects()

        return JSONResponse(data=roots)

API_object_delete.__doc__ = _("""
*Deleting an object.*

#### Request parameters

1. **"app"**     - name of the application, for example: "users";
2. **"model"**   - model name of the application, for example: "user";
3. **"pk"**      - the key of the object model;
4. **"confirm"** - flag confirm the removal;

#### Returned object
If confirmed, or the confirmation is not required:
`Boolean`

If not confirmed, then transferred to the list of dependent objects
that are removed together with this object.

""")


@api_required
@login_required
def API_devices_list(request, **kwargs):
    """
    Получение списка доступных устройств
    """
    data = []
    if site.devices:
        data = site.devices.get_list()
    return JSONResponse(data=data)

API_devices_list.__doc__ = _("""
*Getting a list of available devices.*

#### Request parameters
Nothing

#### Returned object
list of available devices

""")


@api_required
@login_required
def API_devices_exec(request, device, command, params={}, **kwargs):
    """
    Выполнение команды на устройстве
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

API_devices_exec.__doc__ = _("""
*The execution of commands on the device.*

#### Request parameters

1. **"device"**  - device ID;
2. **"command"** - command(method) of device;
3. **"params"**  - parameters for command (default == {});

#### Returned object
the result of the command

""")


_methods = [
    ('bwp.scheme',    'bwp.views.API_bwp_scheme'),
    ('model.objects', 'bwp.views.API_model_objects'),
    ('model.summary', 'bwp.views.API_model_summary'),
    ('model.action',  'bwp.views.API_model_action'),
    ('object.create', 'bwp.views.API_object_create'),
    ('object.read',   'bwp.views.API_object_read'),
    ('object.update', 'bwp.views.API_object_update'),
    ('object.delete', 'bwp.views.API_object_delete'),
    # Test without site.devices:
    #~ ('devices.list', 'bwp.views.API_devices_list'),
    #~ ('devices.exec', 'bwp.views.API_devices_exec'),
]

if hasattr(site, 'devices'):
    _methods.extend([
        ('devices.list', 'bwp.views.API_devices_list'),
        ('devices.exec', 'bwp.views.API_devices_exec'),
    ])

# store prepared methods
METHODS = get_methods(_methods)

@csrf_exempt
def api(request):
    return quickapi_index(request, methods=METHODS)

########################################################################
#                             END API                                  #
########################################################################
