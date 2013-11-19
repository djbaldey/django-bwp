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
from django.conf.urls import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import copy
from bwp.conf import settings
from bwp.sites import site
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

def autodiscover():
    """
    Auto-discover INSTALLED_APPS __bwp__.py modules and fail silently when
    not present. This forces an import on them to register any bwp bits they
    may want.
    """

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        app_label = mod.__name__.split('.')[-1]
        # Attempt to import the app's bwp module.
        try:
            before_apps_list = copy.copy(site.apps_list)
            before_apps = copy.copy(site.apps)
            bwp = import_module('%s.__bwp__' % app)
            if hasattr(mod, '__label__') and app_label in site.apps:
                site.apps[app_label].label = mod.__label__
            elif hasattr(bwp, '__label__') and app_label in site.apps:
                site.apps[app_label].label = bwp.__label__
        except Exception as e:
            #~ print e, app
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            # (see #8245).
            site.apps_list = before_apps_list
            site.apps = before_apps

            # Decide whether to bubble up this error. If the app just
            # doesn't have an bwp module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, '__bwp__'):
                raise

autodiscover()

urlpatterns = patterns('bwp.views',
    url(r'^$',        'index',  name='bwp_index'),
    url(r'^login/$',  'login',  name="bwp_login"),
    url(r'^logout/$', 'logout', name="bwp_logout"),
    url(r'^api/$',    'api',    name="bwp_api"),

    url(r'^upload/(?P<model>[-\.\w]+)/$', 'upload', name="bwp_upload"),
    
    url(r'^accounts/login/$',  'login',  name="bwp_login_redirect"),
    url(r'^accounts/logout/$', 'logout', name="bwp_logout_redirect"),
)

if 'tinymce' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^tinymce/', include('tinymce.urls')),
    )

if 'filebrowser' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^tinymce/filebrowser/', include('filebrowser.urls')),
    )

# For develop:
urlpatterns += staticfiles_urlpatterns()

