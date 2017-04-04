# -*- coding: utf-8 -*-
#
#  bwp/utils/pagers.py
#
#  Copyright 2012 Grigoriy Kramarenko <root@rosix.ru>
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


def page_range_dots(page, on_each_side=3, on_ends=2, dot='.'):
    number = page.number
    num_pages = page.paginator.num_pages
    page_range = page.paginator.page_range
    if num_pages > 9:
        page_range = []
        if number > (on_each_side + on_ends):
            page_range.extend(range(1, on_each_side))
            page_range.append(dot)
            page_range.extend(range(number + 1 - on_each_side, number + 1))
        else:
            page_range.extend(range(1, number + 1))
        if number < (num_pages - on_each_side - on_ends + 1):
            page_range.extend(range(number + 1, number + on_each_side))
            page_range.append(dot)
            page_range.extend(range(num_pages - on_ends + 1, num_pages + 1))
        else:
            page_range.extend(range(number + 1, num_pages + 1))
    return page_range
