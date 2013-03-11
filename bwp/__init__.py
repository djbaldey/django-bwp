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
__version__ = "0.1.2"

def auto_create_version_links():
    """ Автоматически создаёт ссылки на статику по актуальной версии BWP """
    import os
    cwd = os.getcwd()
    self_path = os.path.abspath(os.path.dirname(__file__))
    css_path = os.path.join(self_path, 'static', 'css', 'bwp')
    src_css_path = os.path.join(css_path, 'src')
    ver_css_path = os.path.join(css_path, __version__)
    js_path = os.path.join(self_path, 'static', 'js', 'bwp')
    src_js_path = os.path.join(js_path, 'src')
    ver_js_path = os.path.join(js_path, __version__)
    if not os.path.exists(ver_css_path):
        os.chdir(css_path)
        os.symlink('src', __version__)
    if not os.path.exists(ver_js_path):
        os.chdir(js_path)
        os.symlink('src', __version__)
    os.chdir(cwd)

auto_create_version_links()
