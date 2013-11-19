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
from django.utils.translation import ugettext_lazy as _
__label__ = _('Platform')

VERSION = (0, 5, 0)
__version__ = '.'.join([ str(x) for x in VERSION ])

import django
from django.conf import settings
_django_version_ = float('%s.%s' % (django.VERSION[0], django.VERSION[1]))

if _django_version_ < 1.4:
    raise RuntimeError('To use BWP, '
        'you must use the Django version 1.4 and above. '
        'Running now %s' % django.get_version())

class AuthSettingsError(Exception):
    pass

def check_builtin_users(import_app=False):
    if _django_version_ == 1.4:
        if 'bwp.contrib.users' in settings.INSTALLED_APPS:
            raise AuthSettingsError(
                'To use "bwp.contrib.users" in INSTALLED_APPS, '
                'you must use the Django version 1.5 and above. '
                'Running now %s.' % django.get_version())
        elif not 'django.contrib.auth' in settings.INSTALLED_APPS:
            raise AuthSettingsError(
                'To use "django.contrib.auth", please add this app '
                'in INSTALLED_APPS')
        return False
    elif not 'bwp.contrib.users' in settings.INSTALLED_APPS:
        if import_app:
            raise AuthSettingsError(
                'To use "bwp.contrib.users", please add this app '
                'in INSTALLED_APPS')
        return False
    return True

if check_builtin_users():
    from bwp.contrib.users.models import User, Group, Permission
else:
    from django.contrib.auth.models import User, Group, Permission

def auto_remove_version_links(path):
    for f in os.listdir(path):
        filepath = os.path.join(path, f)
        if os.path.islink(filepath) and f.count('.') == len(VERSION) -1:
            os.unlink(filepath)

def auto_create_version_links():
    """ Автоматически создаёт ссылки на статику по актуальной версии """
    cwd = os.getcwd()
    self_path = os.path.abspath(os.path.dirname(__file__))
    src_relation = os.path.join('..', '..', '..')
    
    src_css_path = os.path.join(src_relation, 'static_src', 'css')
    css_path = os.path.join(self_path, 'static', 'css', 'bwp')
    ver_css_path = os.path.join(css_path, __version__)
    
    src_js_path = os.path.join(src_relation, 'static_src', 'js')
    js_path = os.path.join(self_path, 'static', 'js', 'bwp')
    ver_js_path = os.path.join(js_path, __version__)
    
    if not os.path.exists(ver_css_path):
        auto_remove_version_links(css_path)
        os.chdir(css_path)
        os.symlink(src_css_path, __version__)
    if not os.path.exists(ver_js_path):
        auto_remove_version_links(js_path)
        os.chdir(js_path)
        os.symlink(src_js_path, __version__)
    os.chdir(cwd)

# При сборке пакета и установке через pip код не выполнится
# из-за отсутствия путей.
try:
    auto_create_version_links()
except:
    pass
