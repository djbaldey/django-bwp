# -*- coding: utf-8 -*-
"""
###############################################################################
# Copyright 2012 Grigoriy Kramarenko.
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

def page_range_dots(page, on_each_side=3, on_ends=2, dot='.'):
    number    = page.number
    num_pages = page.paginator.num_pages
    page_range = page.paginator.page_range
    #~ print 0, page_range
    if num_pages > 9:
        page_range = []
        if number > (on_each_side + on_ends):
            page_range.extend(range(1, on_each_side))
            page_range.append(dot)
            page_range.extend(range(number +1 - on_each_side, number + 1))
            #~ print 1, page_range
        else:
            page_range.extend(range(1, number + 1))
            #~ print 2, page_range
        if number < (num_pages - on_each_side - on_ends + 1):
            page_range.extend(range(number + 1, number + on_each_side))
            page_range.append(dot)
            page_range.extend(range(num_pages - on_ends +1, num_pages+1))
            #~ print 3, page_range
        else:
            page_range.extend(range(number + 1, num_pages+1))
    return page_range
