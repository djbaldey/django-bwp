# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
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
