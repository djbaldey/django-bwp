# -*- coding: utf-8 -*-
#
#  bwp/contrib/reports/views.py
#
#  Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import unicode_literals

from django.http import HttpResponseBadRequest

from quickapi.http import JSONResponse
from quickapi.decorators import login_required, api_required

from bwp.contrib.reports.models import Document as Report
from bwp.sites import site


@api_required
@login_required
def API_get_collection_report_url(request, model, report, query=None,
                                  order_by=None, fields=None, filters=None,
                                  **kwargs):
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

    ctx = {'data': qs, 'filters': [x for x in filters if x['active']]}
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

    obj = model_bwp.queryset(request, **kwargs).get(pk=pk)

    ctx = {'data': obj}
    url = report.render_to_media_url(context=ctx, user=request.user)
    return JSONResponse(data=url)
