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
import re
import warnings

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.core import validators
from django.db import models, transaction, DEFAULT_DB_ALIAS
from django.db.models import get_apps, get_models, signals
from django.utils.http import urlquote
from django.utils import six
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import (AbstractBaseUser,
    BaseUserManager, SiteProfileNotAvailable,
    _user_get_all_permissions, _user_has_perm, _user_has_module_perms)

from bwp.conf import GROUP_HARD_KEYS

class ObjectCannotChange(Exception):
    message = ugettext("This object cannot be changed")
class ObjectCannotDelete(Exception):
    message = ugettext("This object cannot be removed")


class PermissionManager(models.Manager):
    def get_by_natural_key(self, codename, app_label, model):
        return self.get(
            codename=codename,
            content_type=ContentType.objects.get_by_natural_key(app_label,
                                                                model),
        )

@python_2_unicode_compatible
class Permission(models.Model):
    """
    The permissions system provides a way to assign permissions to specific
    users and groups of users.

    The permission system is used by the Django admin site, but may also be
    useful in your own code. The Django admin site uses permissions as follows:

        - The "add" permission limits the user's ability to view the "add" form
          and add an object.
        - The "change" permission limits a user's ability to view the change
          list, view the "change" form and change an object.
        - The "delete" permission limits the ability to delete an object.

    Permissions are set globally per type of object, not per specific object
    instance. It is possible to say "Mary may change news stories," but it's
    not currently possible to say "Mary may change news stories, but only the
    ones she created herself" or "Mary may only change news stories that have a
    certain status or publication date."

    Three basic permissions -- add, change and delete -- are automatically
    created for each Django model.
    """
    name = models.CharField(_('name'), max_length=50)
    content_type = models.ForeignKey(ContentType, verbose_name=_('content type'),
        related_name='permissions')
    codename = models.CharField(_('codename'), max_length=100)
    objects = PermissionManager()

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        unique_together = (('content_type', 'codename'),)
        ordering = ('content_type__app_label', 'content_type__model',
                    'codename')

    def __str__(self):
        return "%s | %s | %s" % (
            six.text_type(self.content_type.app_label),
            six.text_type(self.content_type),
            six.text_type(self.name))

    def natural_key(self):
        return (self.codename,) + self.content_type.natural_key()
    natural_key.dependencies = ['contenttypes.contenttype']

class GroupManager(models.Manager):
    """
    The manager for the users Group model.
    """
    def get_by_natural_key(self, name):
        return self.get(name=name)

@python_2_unicode_compatible
class Group(models.Model):
    """
    Groups are a generic way of categorizing users to apply permissions, or
    some other label, to those users. A user can belong to any number of
    groups.

    A user in a group automatically has all the permissions granted to that
    group. For example, if the group Site editors has the permission
    can_edit_home_page, any user in that group will have that permission.

    Beyond permissions, groups are a convenient way to categorize users to
    apply some label, or extended functionality, to them. For example, you
    could create a group 'Special users', and you could write code that would
    do special things to those users -- such as giving them access to a
    members-only portion of your site, or sending them members-only email
    messages.
    """
    HARD_KEYS = GROUP_HARD_KEYS
    name = models.CharField(_('name'), max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission,
        verbose_name=_('permissions'), blank=True)

    objects = GroupManager()

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def save(self, **kwargs):
        # Перезапись жёстко заданных ключей
        if self.pk in Group.HARD_KEYS:
            self.name = Group.HARD_KEYS.get(self.pk)
        super(Group, self).save(**kwargs)

    def delete(self, **kwargs):
        if self.pk in Group.HARD_KEYS:
            raise ObjectCannotDelete(ugettext("This is a hard coded object"))
        super(Group, self).delete(**kwargs)

def update_groups(verbosity=2, db=DEFAULT_DB_ALIAS, **kwargs):
    """
    Create or replace hard groups.
    """
    for pk, name in Group.HARD_KEYS.items():
        group, created = Group.objects.get_or_create(
            pk=pk, defaults={'name': name})
        if not created and group.name != name:
            group.save()

signals.post_syncdb.connect(update_groups)

class UserManager(BaseUserManager):

    def create_user(self, username, password=None, email=None, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        email = UserManager.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_superuser=False, last_login=now,
                          **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        u = self.create_user(username=username, password=password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u

class User(AbstractBaseUser):
    """
    Username, password are required. Other fields are optional.
    The first user in the database always has full rights. 
    """
    ROOT_PK = 1

    created = models.DateTimeField(_('created'), auto_now_add=True, editable=False)
    updated = models.DateTimeField(_('updated'), auto_now=True, editable=False)
    username = models.CharField(_('username'), max_length=50, unique=True)

    email = models.EmailField(_('email address'),blank=True)
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this '
                    'admin site.'))
    is_superuser = models.BooleanField(_('superuser status'), default=False,
        help_text=_('Designates that this user has all permissions without '
                    'explicitly assigning them.'))
    groups = models.ManyToManyField(Group, blank=True,
        verbose_name=_('groups'),
        help_text=_('The groups this user belongs to. A user will '
                    'get all permissions granted to each of '
                    'his/her group.'))
    user_permissions = models.ManyToManyField(Permission, blank=True,
        verbose_name=_('user permissions'),
        help_text='Specific permissions for this user.')

    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    middle_name = models.CharField(_('middle name'), max_length=30, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    #~ REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        if self.middle_name:
            full_name = u'%s %s %s' % (self.first_name, self.middle_name, self.last_name)
        else:
            full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        if not self.last_name and not self.first_name:
            return self.username
        elif self.middle_name:
            return u'%s %s.%s.' % (self.last_name, unicode(self.first_name)[0], unicode(self.middle_name)[0])
        return u'%s %s.' % (self.last_name, unicode(self.first_name)[0])

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def get_group_permissions(self, obj=None):
        """
        Returns a list of permission strings that this user has through his/her
        groups. This method queries all available auth backends. If an object
        is passed in, only permissions matching this object are returned.
        """
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                if obj is not None:
                    permissions.update(backend.get_group_permissions(self,
                                                                     obj))
                else:
                    permissions.update(backend.get_group_permissions(self))
        return permissions

    def get_all_permissions(self, obj=None):
        return _user_get_all_permissions(self, obj)

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user has each of the specified permissions. If
        object is passed, it checks if the user has all required perms for this
        object.
        """
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)

    def save(self, **kwargs):
        # Перезапись основного суперпользователя
        if self.pk == User.ROOT_PK:
            self.is_staff = True
            self.is_active = True
            self.is_superuser = True
        self.last_login = self.last_login or timezone.now()
        super(User, self).save(**kwargs)

    def delete(self, **kwargs):
        if self.pk == User.ROOT_PK:
            raise ObjectCannotDelete(ugettext("This is a root superuser"))
        super(User, self).delete(**kwargs)
