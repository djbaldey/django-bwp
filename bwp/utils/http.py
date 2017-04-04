# -*- coding: utf-8 -*-
#
#  bwp/utils/http.py
#
#  Copyright 2012 Grigoriy Kramarenko <root@rosix.ru>
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
from django.shortcuts import redirect
from django.http import (HttpResponseNotFound, HttpResponseBadRequest,
                         HttpResponseForbidden)

from quickapi.http import JSONResponse


def is_api(request):
    return bool(request.path == redirect('bwp.views.api')['Location'])


def get_http_400(request):
    """ Если запрос на API, то возвращаем JSON, иначе обычный ответ """
    if is_api(request):
        return JSONResponse(status=400)
    return HttpResponseBadRequest()


def get_http_403(request):
    """ Если запрос на API, то возвращаем JSON, иначе обычный ответ """
    if is_api(request):
        return JSONResponse(status=404)
    return HttpResponseForbidden()


def get_http_404(request):
    """ Если запрос на API, то возвращаем JSON, иначе обычный ответ """
    if is_api(request):
        return JSONResponse(status=404)
    return HttpResponseNotFound()
