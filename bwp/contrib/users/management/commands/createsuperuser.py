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

Management utility to create superusers.
"""

import getpass
import sys
from optparse import make_option

from django.contrib.auth import get_user_model
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.utils.encoding import force_str, force_text
from django.utils.six.moves import input
from django.utils.text import capfirst

from bwp.contrib.users.management import get_default_username

class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        # Options are defined in an __init__ method to support swapping out
        # custom user models in tests.
        super(Command, self).__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(self.UserModel.USERNAME_FIELD)

        self.option_list = BaseCommand.option_list + (
            make_option('--%s' % self.UserModel.USERNAME_FIELD, dest=self.UserModel.USERNAME_FIELD, default=None,
                help='Specifies the login for the superuser.'),
            make_option('--noinput', action='store_false', dest='interactive', default=True,
                help=('Tells Django to NOT prompt the user for input of any kind. '
                    'You must use --%s with --noinput, along with an option for '
                    'any other required field. Superusers created with --noinput will '
                    ' not be able to log in until they\'re given a valid password.' %
                    self.UserModel.USERNAME_FIELD)),
            make_option('--database', action='store', dest='database',
                default=DEFAULT_DB_ALIAS, help='Specifies the database to use. Default is "default".'),
        ) + tuple(
            make_option('--%s' % field, dest=field, default=None,
                help='Specifies the %s for the superuser.' % field)
            for field in self.UserModel.REQUIRED_FIELDS
        )

    option_list = BaseCommand.option_list
    help = 'Used to create a superuser.'

    def handle(self, *args, **options):
        username = options.get(self.UserModel.USERNAME_FIELD, None)
        interactive = options.get('interactive')
        verbosity = int(options.get('verbosity', 1))
        database = options.get('database')

        # If not provided, create the user with an unusable password
        password = None
        user_data = {}

        # Do quick and dirty validation if --noinput
        if not interactive:
            try:
                if not username:
                    raise CommandError("You must use --%s with --noinput." %
                            self.UserModel.USERNAME_FIELD)
                username = self.username_field.clean(username, None)

                for field_name in self.UserModel.REQUIRED_FIELDS:
                    if options.get(field_name):
                        field = self.UserModel._meta.get_field(field_name)
                        user_data[field_name] = field.clean(options[field_name], None)
                    else:
                        raise CommandError("You must use --%s with --noinput." % field_name)
            except exceptions.ValidationError as e:
                raise CommandError('; '.join(e.messages))

        else:
            # Prompt for username/password, and any other required fields.
            # Enclose this whole thing in a try/except to trap for a
            # keyboard interrupt and exit gracefully.
            default_username = get_default_username()
            try:

                # Get a username
                verbose_field_name = force_text(self.username_field.verbose_name)
                while username is None:
                    if not username:
                        input_msg = capfirst(verbose_field_name)
                        if default_username:
                            input_msg = "%s (leave blank to use '%s')" % (
                                input_msg, default_username)
                        raw_value = input(force_str('%s: ' % input_msg))

                    if default_username and raw_value == '':
                        raw_value = default_username
                    try:
                        username = self.username_field.clean(raw_value, None)
                    except exceptions.ValidationError as e:
                        self.stderr.write("Error: %s" % '; '.join(e.messages))
                        username = None
                        continue
                    try:
                        self.UserModel._default_manager.db_manager(database).get_by_natural_key(username)
                    except self.UserModel.DoesNotExist:
                        pass
                    else:
                        self.stderr.write("Error: That %s is already taken." %
                                verbose_field_name)
                        username = None

                for field_name in self.UserModel.REQUIRED_FIELDS:
                    field = self.UserModel._meta.get_field(field_name)
                    user_data[field_name] = options.get(field_name)
                    while user_data[field_name] is None:
                        raw_value = input(force_str('%s: ' % capfirst(force_text(field.verbose_name))))
                        try:
                            user_data[field_name] = field.clean(raw_value, None)
                        except exceptions.ValidationError as e:
                            self.stderr.write("Error: %s" % '; '.join(e.messages))
                            user_data[field_name] = None

                # Get a password
                while password is None:
                    if not password:
                        password = getpass.getpass()
                        password2 = getpass.getpass(force_str('Password (again): '))
                        if password != password2:
                            self.stderr.write("Error: Your passwords didn't match.")
                            password = None
                            continue
                    if password.strip() == '':
                        self.stderr.write("Error: Blank passwords aren't allowed.")
                        password = None
                        continue

            except KeyboardInterrupt:
                self.stderr.write("\nOperation cancelled.")
                sys.exit(1)

        user_data[self.UserModel.USERNAME_FIELD] = username
        user_data['password'] = password
        self.UserModel._default_manager.db_manager(database).create_superuser(**user_data)
        if verbosity >= 1:
            self.stdout.write("Superuser created successfully.")
