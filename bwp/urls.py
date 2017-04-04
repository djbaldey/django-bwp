# -*- coding: utf-8 -*-
#
#  bwp/urls.py
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
from django.conf import settings
from django.conf.urls import url

from bwp.views import index, login, logout, upload, api


urlpatterns = [
    url(r'^$', index, name='bwp_index'),
    url(r'^login/$', login, name="bwp_login"),
    url(r'^logout/$', logout, name="bwp_logout"),
    url(r'^api/$', api, name="bwp_api"),
    url(r'^upload/(?P<model>[-\.\w]+)/$', upload, name="bwp_upload"),
    url(r'^accounts/login/$', login, name="bwp_login_redirect"),
    url(r'^accounts/logout/$', logout, name="bwp_logout_redirect"),
]


# For develop:
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
