# -*- coding: utf-8 -*-
#
#  bwp/utils/version.py
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
import os
from bwp import __version__, VERSION


def auto_remove_version_links(path):
    for f in os.listdir(path):
        filepath = os.path.join(path, f)
        if os.path.islink(filepath) and f.count('.') == len(VERSION) - 1:
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
