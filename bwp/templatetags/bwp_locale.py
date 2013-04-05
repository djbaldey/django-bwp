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
from django.template import Library
from bwp.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst

APP_LABELS = getattr(settings, 'APP_LABELS',
    {
        'admin':            _('administration'),
        'auth':             _('authentication'),
        'sites':            _('sites'),
        'contenttypes':     _('content types'),
    }
)

register = Library()

@register.simple_tag
#~ @register.filter
def app_label_locale(app_name):
    # Оригинальное написание
    if   app_name == app_name.title():   writing = lambda(x): x.title()
    elif app_name == capfirst(app_name): writing = lambda(x): x.title()
    elif app_name == app_name.upper():   writing = lambda(x): x.upper()
    elif app_name == app_name.lower():   writing = lambda(x): x.lower()
    else:                                writing = lambda(x): x

    # Список приложений Django
    try:
        return writing(APP_LABELS[app_name.lower()])
    except:
        pass

    # Список приложений BWP
    for app in settings.INSTALLED_APPS:
        if app_name.lower() in app.lower():
            L = app.split('.')
            if len(L) == 1:
                try:
                    app = __import__(app, fromlist=[''])
                except Exception as e:
                    print e
            elif len(L) >= 2:
                try:
                    module = __import__('.'.join(L[:-1]), fromlist=[''])
                    app = getattr(module, L[-1])
                except Exception as e:
                    print e
            try:
                return writing(app.__label__)
            except Exception as e:
                print app.__name__, e
                return app_name
    return app_name
