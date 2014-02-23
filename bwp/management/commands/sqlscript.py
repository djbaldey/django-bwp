# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2014 Grigoriy Kramarenko.
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
from django.utils.importlib import import_module
from django.core.management.base import LabelCommand
from django.utils.translation import ugettext_lazy as _
from django.db import connections, transaction, DEFAULT_DB_ALIAS

from bwp.conf import settings

def prepare_engine(engine):
    engine = engine.split('.')[-1]
    for e in ('postgresql', 'mysql', 'sqlite', 'oracle'):
        if engine.count(e):
            return e
    return engine

DATABASE_ENGINES = [ (x,prepare_engine(y['ENGINE'])) for x,y in settings.DATABASES.items() ]

def _prepare_sql(lines):
    L = []
    for line in lines:
        l = line.lstrip(' ')
        if not l or l == '\n':
            continue
        elif l.startswith('--'):
            continue
        L.append(line)
    L[-1] = L[-1].replace(';\n', ';')
    sql = '\n'.join(L).replace('\n\n', '\n')
    return sql.decode(settings.FILE_CHARSET)


def sql_custom(db):
    "Returns a list of the custom table modifying SQL statements for the given db alias."
    output = []
    D = dict(DATABASE_ENGINES)
    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        _dir = os.path.normpath(os.path.join(os.path.dirname(mod.__file__), 'sql', 'bases'))
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
    help = ("Prints the joined all custom SQL scripts for the given database alias.\n"
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
