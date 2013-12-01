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
from django.utils.translation import ugettext_lazy as _
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import capfirst

from bwp.models import ModelBWP
from bwp.forms import BWPAuthenticationForm
from bwp import conf
from bwp.conf import settings
from bwp.templatetags.bwp_locale import app_label_locale

SORTING_APPS_LIST = getattr(conf, 'SORTING_APPS_LIST', True)
APP_LABELS        = getattr(conf, 'APP_LABELS',
    {
        'admin':            _('Administration'),
        'auth':             _('Users'),
        'sites':            _('Sites'),
        'contenttypes':     _('Content types'),
    }
)

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class AppBWP(object):
    """ Класс приложения для регистрации BWP-моделей """

    def __init__(self, site, icon=None, label=''):
        self.site = site
        self.icon = icon
        self.label = label
        self.models_list = []
        self.models = {}

    def has_permission(self, request):
        """
        Возвращает True, если данный HttpRequest имеет разрешение на
        просмотр по крайней мере одной модели в приложении
        """
        def check_models():
            for model in self.models.values():
                if model.has_permission(request):
                    return True
            return False
        return check_models()

    def get_available_models(self, request):
        """ Возвращает модели, доступные для пользователя """
        models = {}
        for name, model in self.models.items():
            if model.has_permission(request):
                models[name] = model
        return models

    def get_scheme(self, request):
        """ Возвращает схему приложения для пользователя """
        APP = {
            'icon': self.icon,
            'label': self.label,
            'models_list':[],
            'models':{},
        }
        for name in self.models_list:
            if not name:
                # TODO: чтобы использовать разделители, нужно реализовать 
                # site.register_model(...)
                # site.unregister_model(...)
                APP['models_list'].append(None)
            else:
                model = self.models[name]
                scheme = model.get_scheme(request)
                if scheme:
                    APP['models_list'].append(name)
                    APP['models'][name] = scheme
        return APP

class SiteBWP(object):
    """ Класс сайта для регистрации приложений BWP, панели приборов,
        меню, локальных устройств и прочего.
    """

    def __init__(self, icon=None, label=_('BWP')):
        self._registry = {} # model_class class -> bwp_class instance
        self.icon = icon
        self.label = label

        self.dashboard  = None # экземпляр DashboardBWP
        self.reports    = {}
        self.apps_list  = []   # меню приложений AppBWP
        self.apps       = {}   # экземпляры AppBWP
        self.devices    = None # local devices, such as
                               # fiscal register, receipt printer, etc.

    def register_model(self, itermodel, bwp_class=None, separator=False, **options):
        """
        Registers the given model(s) with the given bwp class.

        The model(s) should be Model classes, not instances.

        If an bwp class isn't given, it will use ModelBWP (the default
        bwp options). If keyword arguments are given -- e.g., list_display --
        they'll be applied as options to the bwp class.

        If a model is already registered, this will raise AlreadyRegistered.

        If a model is abstract, this will raise ImproperlyConfigured.
        """
        if not bwp_class:
            bwp_class = ModelBWP

        # Don't import the humongous validation code unless required
        if bwp_class and settings.DEBUG:
            from bwp.validation import validate
        else:
            validate = lambda model, bwpclass: None
        validate = lambda model, bwpclass: None

        if isinstance(itermodel, ModelBase):
            itermodel = [itermodel]

        for model in itermodel:

            meta = model._meta

            if meta.abstract:
                raise ImproperlyConfigured('The model %s is abstract, so it '
                      'cannot be registered with bwp.' % model.__name__)

            app_label = meta.app_label
            model_name = getattr(meta, 'model_name',  meta.object_name.lower()) 
            if not app_label in self.apps:
                self.apps[app_label] = AppBWP(
                    site=self,
                    icon=None, # TODO: сделать чтение из __init__.py
                    label=APP_LABELS.get(app_label, _(app_label)),
                    )
                self.apps_list.append(app_label)
            app = self.apps[app_label]

            if model in app.models:
                raise AlreadyRegistered('The model %s is already registered' % model.__name__)

            # If we got **options then dynamically construct a subclass of
            # bwp_class with those **options.
            if options:
                # For reasons I don't quite understand, without a __module__
                # the created class appears to "live" in the wrong place,
                # which causes issues later on.
                options['__module__'] = __name__
                bwp_class = type("%sBWP" % model.__name__, (bwp_class,), options)

            # Validate (which might be a no-op)
            validate(bwp_class, model)

            # Instantiate the bwp class to save in the registry
            app.models[model_name] = bwp_class(model, self)

            # Регистрируем разделитель в списке моделей
            # TODO: чтобы использовать разделители, нужно реализовать 
            # self.unregister_model(...)
            #~ if separator:
                #~ app.models_list.append(None)
            # Регистрируем модель в списке
            app.models_list.append(model_name)

            # В модели делаем ссылку на сайт, это нужно для доступа к нему
            model.site = self

    # Deprecated
    def register(self, *args, **kwargs):
        return self.register_model(*args, **kwargs)

    def unregister_model(self, itermodel):
        """
        Unregisters the given model(s).

        If a model isn't already registered, this will raise NotRegistered.
        """
        if isinstance(itermodel, ModelBase):
            itermodel = [itermodel]
        for model in itermodel:
            meta = model._meta
            app_label = meta.app_label
            model_name = getattr(meta, 'model_name',  meta.object_name.lower()) 

            if app_label not in self.apps or model_name not in self.apps[app_label].models:
                raise NotRegistered('The model %s is not registered' % model.__name__)

            app = self.apps[app_label]
            free_model = app.models.pop(model_name)

            if model_name in app.models_list:
                del app.models_list[app.models_list.index(model_name)]

            if not app.models.keys():
                del self.apps[app_label]
                del self.apps_list[self.apps_list.index(app_label)]

            return free_model

    # Deprecated
    def unregister(self, *args, **kwargs):
        return self.unregister_model(*args, **kwargs)

    def has_permission(self, request):
        """
        Returns True if the given HttpRequest has permission to view
        *at least one* page in the bwp site.
        """
        return request.user.is_active and request.user.is_staff

    def check_dependencies(self):
        """
        Check that all things needed to run the bwp have been correctly installed.

        The default implementation checks that LogEntry, ContentType and the
        auth context processor are installed.
        """
        from django.contrib.contenttypes.models import ContentType

        if 'quickapi' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured("Put 'quickapi' in your "
                "INSTALLED_APPS setting in order to use the bwp application.")

        #~ if 'django.contrib.admin' in settings.INSTALLED_APPS:
            #~ raise ImproperlyConfigured("Remove 'django.contrib.admin' in your "
                #~ "INSTALLED_APPS setting in order to use the bwp application.")
        if not ContentType._meta.installed:
            raise ImproperlyConfigured("Put 'django.contrib.contenttypes' in "
                "your INSTALLED_APPS setting in order to use the bwp application.")
        if not ('django.contrib.auth.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS or
            'django.core.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS):
            raise ImproperlyConfigured("Put 'django.contrib.auth.context_processors.auth' "
                "in your TEMPLATE_CONTEXT_PROCESSORS setting in order to use the bwp application.")

    #~ def get_available_apps(self, request):
        #~ """ Возвращает приложения, доступные для пользователя """
        #~ apps = {}
        #~ for name, app in self.apps.items():
            #~ if app.has_permission(request):
                #~ apps[name] = app
        #~ return apps

    def get_scheme(self, request=None):
        """ Возвращает схему приложения, доступную для пользователя и 
            состоящую из простых объектов Python, готовых к
            сериализации в любую структуру
        """

        SCHEME = {
            'icon': self.icon,
            'label': self.label,
            'dashboard': [],
            'reports': {},
            'apps': {},
        }

        apps_list = []

        for name in self.apps_list:
            app = self.apps[name]
            scheme = app.get_scheme(request)
            if scheme:
                apps_list.append((name, unicode(app.label)))
                SCHEME['apps'][name] = scheme

        if SORTING_APPS_LIST:
            apps_list = sorted(apps_list, key=lambda x: x[1])

        SCHEME['apps_list'] = [ x[0] for x in apps_list ]
        SCHEME['settings'] = self.get_scheme_settings(request)

        return SCHEME

    def get_scheme_settings(self, request):
        """ Возвращает схему настроек пользователя """
        # TODO: реализовать
        SETTINGS = {}
        return SETTINGS

    def get_registry_devices(self, request=None):
        """
        Общий метод для проверки привилегий на объекты устройств. 
        
        Если не задан запрос, то возвращает весь список, без учёта
        привилегий.
        """
        if self.devices is None:
            return []
        if request is None: 
            return self.devices
        available = []
        for device in self.devices:
            if device.has_permission(request) or device.has_admin_permission(request):
                available.append(device)
        return available

    def devices_dict(self, request):
        """
        Возвращает словарь, где ключом является название устройства,
        а значением - само устройство
        """
        return dict([ (device.title, device) \
            for device in self.get_registry_devices(request)
        ])


# This global object represents the default bwp site, for the common case.
# You can instantiate SiteBWP in your own code to create a custom bwp site.
site = SiteBWP()
