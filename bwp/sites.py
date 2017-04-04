# -*- coding: utf-8 -*-
#
#  bwp/sites.py
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

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.utils.module_loading import autodiscover_modules
from django.utils.text import capfirst

from bwp.models import ModelBWP
from bwp.templatetags.bwp_locale import app_label_locale


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class BWPSite(object):
    """ Класс объекта для регистрации моделей в BWP из одного экземпляра """

    # local devices, such as fiscal register, receipt printer, etc.
    devices = None

    def __init__(self, name='bwp', app_name='bwp'):
        # model_class class -> bwp_class instance
        self._registry = {}
        self.name = name
        self.app_name = app_name

    def register(self, model_or_iterable, bwp_class=None, **options):
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
        # if bwp_class and settings.DEBUG:
        #     from bwp.validation import validate
        # else:
        #     def validate(model, bwpclass):
        #         return None

        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model._meta.abstract:
                raise ImproperlyConfigured(
                    'The model %s is abstract, so it '
                    'cannot be registered with bwp.' % model.__name__)

            if model in self._registry:
                raise AlreadyRegistered(
                    'The model %s is already registered' % model.__name__)

            # If we got **options then dynamically construct a subclass of
            # bwp_class with those **options.
            if options:
                # For reasons I don't quite understand, without a __module__
                # the created class appears to "live" in the wrong place,
                # which causes issues later on.
                options['__module__'] = __name__
                bwp_class = type(
                    "%sBWP" % model.__name__, (bwp_class,), options
                )

            # Validate (which might be a no-op)
            # validate(bwp_class, model)

            # Instantiate the bwp class to save in the registry
            self._registry[model] = bwp_class(model, self)

            # В модели делаем ссылку на сайт, это нужно для доступа к нему
            model.site = self

    def unregister(self, model_or_iterable):
        """
        Unregisters the given model(s).

        If a model isn't already registered, this will raise NotRegistered.
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                raise NotRegistered(
                    'The model %s is not registered' % model.__name__)
            del self._registry[model]

    def has_permission(self, request):
        """
        Returns True if the given HttpRequest has permission to view
        *at least one* page in the bwp site.
        """
        return request.user.is_active and request.user.is_staff

    def check_dependencies(self):
        """
        Check that all things needed to run the bwp have been correctly
        installed.

        The default implementation checks that LogEntry, ContentType and the
        auth context processor are installed.
        """
        from django.contrib.contenttypes.models import ContentType

        if 'quickapi' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "Put 'quickapi' in your "
                "INSTALLED_APPS setting in order to use the bwp application.")

        if not ContentType._meta.installed:
            raise ImproperlyConfigured(
                "Put 'django.contrib.contenttypes' in "
                "your INSTALLED_APPS setting in order to "
                "use the bwp application.")
        if not ('django.contrib.auth.context_processors.auth' in
                settings.TEMPLATE_CONTEXT_PROCESSORS or
                'django.core.context_processors.auth' in
                settings.TEMPLATE_CONTEXT_PROCESSORS):
            raise ImproperlyConfigured(
                "Put 'django.contrib.auth.context_processors.auth' "
                "in your TEMPLATE_CONTEXT_PROCESSORS setting in order "
                "to use the bwp application.")

    def get_registry_items(self, request=None):
        """
        Общий метод для проверки привилегий на объекты моделей BWP
        и моделей приложений.

        Если не задан запрос, то возвращает весь список, без учёта
        привилегий.
        """
        if request is None:
            return self._registry.items()
        available = []
        for model, model_bwp in self._registry.items():
            perms = model_bwp.get_model_perms(request)
            if True in perms.values():
                available.append((model, model_bwp))
        return available

    def bwp_dict(self, request):
        """
        Возвращает словарь, где ключом является имя модели BWP,
        а значением - сама модель, например:
            {'auth.user': <Model Contacts.UserBWP> }
        """
        return dict([
            (str(model._meta), model_bwp) for model, model_bwp in
            self.get_registry_items(request)
        ])

    def model_dict(self, request):
        """
        Возвращает словарь, где ключом является имя модели приложения,
        а значением - сама модель, например:
            {'auth.user':<Model Auth.User>,}
        """
        return dict([
            (str(model._meta), model) for model, model_bwp in
            self.get_registry_items(request)
        ])

    def app_dict(self, request):
        """
        Возвращает сложный словарь, где первым ключом является имя
        приложения, его значением словарь с ключом `models` - список
        вложенных моделей:
        {'auth': { 'models':[<Model Auth.User>,<Model Auth.Group>], ...}
        """
        app_dict = {}
        for model, model_bwp in self.get_registry_items(request):
            app_label = model._meta.app_label
            has_module_perms = request.user.has_module_perms(app_label)

            # Разрешения уже проверены в методе get_registry_items(request)
            model_dict = model_bwp.get_model_info(request, bwp=True)

            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': app_label,
                    'label': app_label_locale(capfirst(app_label)),
                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                }
        return app_dict

    def app_list(self, request):
        """
        Возвращает отсортированный по названию список моделей приложений.
        """
        # Sort the apps alphabetically.
        app_list = self.app_dict(request).values()
        app_list.sort(key=lambda x: x['label'])

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['label'])

        return app_list

    def serialize(self, request):
        """ Сериализует все объекты сайта в Python """
        app_list = self.app_list(request)
        # Удаляем модели BWP из словарей
        for app in app_list:
            for dicmodel in app['models']:
                dicmodel.pop('bwp')
        return app_list

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
            if (device.has_permission(request) or
                    device.has_admin_permission(request)):
                available.append(device)
        return available

    def devices_dict(self, request):
        """
        Возвращает словарь, где ключом является название устройства,
        а значением - само устройство
        """
        return dict([
            (device.title, device) for device in
            self.get_registry_devices(request)
        ])


# This global object represents the default bwp site, for the common case.
# You can instantiate BWPSite in your own code to create a custom bwp site.
site = BWPSite()


def autodiscover():
    autodiscover_modules('__bwp__', register_to=site)
