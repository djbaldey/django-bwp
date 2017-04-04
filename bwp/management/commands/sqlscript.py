# -*- coding: utf-8 -*-
#
#  bwp/management/commands/sqlscript.py
#
#  Copyright 2014 Grigoriy Kramarenko <root@rosix.ru>
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
import os
from django.utils.importlib import import_module
from django.core.management.base import LabelCommand
from django.db import DEFAULT_DB_ALIAS

from bwp.conf import settings


def prepare_engine(engine):
    engine = engine.split('.')[-1]
    for e in ('postgresql', 'mysql', 'sqlite', 'oracle'):
        if engine.count(e):
            return e
    return engine


DATABASE_ENGINES = [
    (x, prepare_engine(y['ENGINE'])) for x, y in settings.DATABASES.items()
]


def _prepare_sql(lines):
    L = []
    for line in lines:
        line = line.lstrip(' ')
        if not line or line == '\n':
            continue
        elif line.startswith('--'):
            continue
        L.append(line)
    L[-1] = L[-1].replace(';\n', ';')
    sql = '\n'.join(L).replace('\n\n', '\n')
    return sql.decode(settings.FILE_CHARSET)


def sql_custom(db):
    """Returns a list of the custom table modifying SQL statements for
    the given db alias."""
    output = []
    D = dict(DATABASE_ENGINES)
    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        _dir = os.path.normpath(
            os.path.join(
                os.path.dirname(mod.__file__),
                'sql',
                'bases'
            )
        )
        custom_files = [os.path.join(_dir, "all.sql")]
        custom_files.append(os.path.join(_dir, "%s.sql" % D.get(db, '')))
        custom_files.append(os.path.join(_dir, db, "all.sql"))
        custom_files.append(os.path.join(_dir, db, "%s.sql" % D.get(db, '')))
        for custom_file in custom_files:
            if os.path.exists(custom_file):
                fp = open(custom_file, 'U')
                output.append(fp.read().decode(settings.FILE_CHARSET))
                fp.close()

    return output


class Command(LabelCommand):
    help = (
        "Prints the joined all custom SQL scripts for the given "
        "database alias.\n"
        "\nExample direct run script in database:\n"
        "./manage.py sqlscript | ./manage.py dbshell\n"
        "OR\n"
        "./manage.py sqlscript master | ./manage.py dbshell --database=master"
    )
    args = '<db_alias_1 db_alias_2 ...>'
    label = 'db_alias'

    output_transaction = False

    def handle(self, *labels, **options):
        output = []
        if not labels:
            label_output = self.handle_label(DEFAULT_DB_ALIAS, **options)
            if label_output:
                output.append(label_output)
        else:
            for label in labels:
                label_output = self.handle_label(label, **options)
                if label_output:
                    output.append(label_output)
        return '\n'.join(output)

    def handle_label(self, label, **options):
        return u'\n'.join(sql_custom(label)).encode('utf-8') + '\n'
