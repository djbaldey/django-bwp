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
import os

from django.http import HttpResponse
from django.template import Context
from bwp.contrib.webodt.cache import CacheManager
from bwp.contrib.webodt.converters import converter
from bwp.contrib.webodt.helpers import get_mimetype

from bwp.contrib import webodt

def render_to(format, template_name,
        dictionary=None, context_instance=None, delete_on_close=True,
        cache=CacheManager, preprocessors=None
    ):
    """
    Convert the template given by `template_name` and `dictionary` to a
    document in given `format`. The document (file-like object) will be
    returned.

    `format` is the filename extension. It's possible to use "odt", "pdf",
    "doc", "html" or "rtf" and probably more.

    `context_instance` is the optional parameter which should contain
    instance of the subclass of `django.template.Context`.

    `delete_on_close` defines whether the returned document should be deleted
    automatically when closed.

    `preprocessors` is a list of preprocessors overriding
    ``WEBODT_ODF_TEMPLATE_PREPROCESSORS`` settings variable.
    Suitable for ODF documents only.

    If the `template_name` ends with `.html`, template is considered as HTML
    template, otherwise as ODF based template.
    """
    template = _Template(template_name, preprocessors=preprocessors)
    dictionary = dictionary or {}
    if context_instance:
        context_instance.update(dictionary)
    else:
        context_instance = Context(dictionary)
    document = template.render(context_instance, delete_on_close=delete_on_close)
    if format == 'odt':
        return document
    formatted_document = None
    if cache:
        cache_mgr = cache()
        formatted_document = cache_mgr.get(document, format)
    if not formatted_document:
        formatted_document = converter().convert(document, format, delete_on_close=delete_on_close)
        cache_mgr.set(document, format, formatted_document)
    document.close()
    return formatted_document


def render_to_response(template_name,
        dictionary=None, context_instance=None, filename=None, format='odt',
        cache=CacheManager, preprocessors=None, inline=None
    ):
    """
    Using same options as `render_to`, return `django.http.HttpResponse`
    object. The document is automatically removed when the last byte of the
    response is read.
    """
    mimetype = get_mimetype(format)
    content_fd = render_to(format, template_name, dictionary, context_instance,
        delete_on_close=True, cache=cache, preprocessors=preprocessors
    )
    response = HttpResponse(_ifile(content_fd), mimetype=mimetype)
    if not filename:
        filename = os.path.basename(template_name)
        filename += '.%s' % format
    response['Content-Disposition'] = (
        inline and 'inline' or 'attachment; filename="%s"' % filename
    )
    return response


def _Template(template_name, preprocessors):
    if template_name.endswith('.html'):
        return webodt.HTMLTemplate(template_name)
    return webodt.ODFTemplate(template_name, preprocessors=preprocessors)


def _ifile(fd, chunk_size=1024, close_on_exit=True):
    while True:
        data = fd.read(chunk_size)
        if not data:
            if close_on_exit:
                fd.close()
            break
        else:
            yield data
