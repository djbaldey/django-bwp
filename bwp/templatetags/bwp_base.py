# -*- coding: utf-8 -*-
#
#  bwp/templatetags/bwp_base.py
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
from django import VERSION
from django.core.urlresolvers import reverse
from django.template import Library, TemplateSyntaxError
from django.template.defaulttags import kwarg_re, URLNode
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bwp import conf
from bwp.utils.datetimes import datetime_server_naive

register = Library()


@register.simple_tag
def SETTINGS(key):
    return getattr(conf, key, getattr(conf.settings, key, ''))


@register.simple_tag
def DEMO():
    mode = getattr(conf, 'DEMO', getattr(conf.settings, 'DEMO', False))
    if mode:
        return '<span class="label label-important">DEMO</span>'
    return ''


@register.simple_tag
def mini_library():
    if conf.settings.DEBUG:
        return ''
    return '.min'


@register.simple_tag
def AUTHORS():
    try:
        return ' | '.join(conf.AUTHORS).strip()
    except:
        return ''


@register.simple_tag
def COPYRIGHT_YEARS():
    end = timezone.now().date().year
    try:
        start = conf.COPYRIGHT_YEAR
    except:
        start = end
    if str(start) != str(end):
        return "%s-%s" % (start, end)
    else:
        return "%s" % end


@register.simple_tag
def SERVER_TZ_OFFSET_JS():
    """
    Offset from UTC as JavaScript style
    """
    offset = SETTINGS('SERVER_TZ_OFFSET_JS') or None
    if offset is not None:
        return offset
    tz = timezone.get_current_timezone()
    sec = tz.utcoffset(datetime_server_naive()).total_seconds()
    return int(sec / 60) * -1


@register.simple_tag
def navactive(request, urls):
    if request.path in [reverse(url) for url in urls.split()]:
        return "active"
    return ""


@register.simple_tag
def subnavactive(request, key, val=None):
    if val is None and (key in request.GET):
        return "active"
    if (val in ('', 0)) and (key not in request.GET):
        return "active"
    if key in request.GET:
        if isinstance(val, int):
            try:
                get_val = int(request.GET.get(key))
            except:
                get_val = None
        if isinstance(val, str):
            try:
                get_val = str(request.GET.get(key))
            except:
                get_val = None
        if get_val == val:
            return "active"
    return ""


@register.simple_tag
def addGET(request, key, val=''):
    dic = request.GET.copy()
    if val:
        dic[key] = val
    else:
        try:
            del dic[key]
        except:
            pass
    L = ['%s=%s' % (k, v) for k, v in dic.items()]
    return "?" + '&'.join(L)


@register.simple_tag
def short_username(user):
    if user.is_anonymous():
        return _('Anonymous')
    if not user.last_name and not user.first_name:
        return user.username
    return u'%s %s.' % (user.last_name, unicode(user.first_name)[0])


@register.simple_tag
def full_username(user):
    if user.is_anonymous():
        return _('Anonymous')
    if not user.last_name and not user.first_name:
        return user.username
    return u'%s %s' % (user.last_name, user.first_name)


@register.filter
def is_active(qs):
    try:
        return qs.filter(is_active=True)
    except:
        return qs


@register.filter
def split(obj, string):
    return obj.split(string)


@register.simple_tag
def pagination(request, paginator):
    """ paginator.paginator.count
        paginator.paginator.num_pages
        paginator.paginator.page_range
        paginator.object_list
        paginator.number
        paginator.has_next()
        paginator.has_previous()
        paginator.has_other_pages()
        paginator.next_page_number()
        paginator.previous_page_number()
        paginator.start_index()
        paginator.end_index()
    """
    temp = '<li class="%s"><a href="%s">%s</a></li>'
    number = paginator.number
    num_pages = paginator.paginator.num_pages
    DOT = '.'
    ON_EACH_SIDE = 3
    ON_ENDS = 2
    page_range = paginator.paginator.page_range
    if num_pages > 9:
        page_range = []
        if number > (ON_EACH_SIDE + ON_ENDS):
            page_range.extend(range(1, ON_EACH_SIDE))
            page_range.append(DOT)
            page_range.extend(range(number + 1 - ON_EACH_SIDE, number + 1))
        else:
            page_range.extend(range(1, number + 1))
        if number < (num_pages - ON_EACH_SIDE - ON_ENDS + 1):
            page_range.extend(range(number + 1, number + ON_EACH_SIDE))
            page_range.append(DOT)
            page_range.extend(range(num_pages - ON_ENDS + 1, num_pages + 1))
        else:
            page_range.extend(range(number + 1, num_pages + 1))
    L = []
    for num in page_range:
        css = ""
        link = '#'
        if num == DOT:
            css = "disabled"
            num = '...'
        elif num == paginator.number:
            css = "active"
        else:
            link = addGET(request, 'page', num)
        L.append(temp % (css, link, num))
    return u''.join(L)


@register.filter
def multiply(obj, digit):
    if obj is None:
        return 0
    try:
        return obj * digit
    except:
        return 'filter error'


@register.filter
def divide(obj, digit):
    if obj is None or digit == 0:
        return 0
    try:
        return 1.0 * obj / digit
    except:
        return 'filter error'


if VERSION[1] <= 5:
    @register.tag
    def feature_url(parser, token):
        """
        Returns an absolute URL matching given view with its parameters.

        This is a way to define links that aren't tied to a particular URL
        configuration::

            {% url "path.to.some_view" arg1 arg2 %}

            or

            {% url "path.to.some_view" name1=value1 name2=value2 %}

        The first argument is a path to a view. It can be an absolute Python path
        or just ``app_name.view_name`` without the project name if the view is
        located inside the project.

        Other arguments are space-separated values that will be filled in place of
        positional and keyword arguments in the URL. Don't mix positional and
        keyword arguments.

        All arguments for the URL should be present.

        For example if you have a view ``app_name.client`` taking client's id and
        the corresponding line in a URLconf looks like this::

            ('^client/(\d+)/$', 'app_name.client')

        and this app's URLconf is included into the project's URLconf under some
        path::

            ('^clients/', include('project_name.app_name.urls'))

        then in a template you can create a link for a certain client like this::

            {% url "app_name.client" client.id %}

        The URL will look like ``/clients/client/123/``.

        The first argument can also be a named URL instead of the Python path to
        the view callable. For example if the URLconf entry looks like this::

            url('^client/(\d+)/$', name='client-detail-view')

        then in the template you can use::

            {% url "client-detail-view" client.id %}

        There is even another possible value type for the first argument. It can be
        the name of a template variable that will be evaluated to obtain the view
        name or the URL name, e.g.::

            {% with view_path="app_name.client" %}
            {% url view_path client.id %}
            {% endwith %}

            or,

            {% with url_name="client-detail-view" %}
            {% url url_name client.id %}
            {% endwith %}

        """
        bits = token.split_contents()
        if len(bits) < 2:
            raise TemplateSyntaxError("'%s' takes at least one argument"
                                      " (path to a view)" % bits[0])
        viewname = parser.compile_filter(bits[1])
        args = []
        kwargs = {}
        asvar = None
        bits = bits[2:]
        if len(bits) >= 2 and bits[-2] == 'as':
            asvar = bits[-1]
            bits = bits[:-2]

        if len(bits):
            for bit in bits:
                match = kwarg_re.match(bit)
                if not match:
                    raise TemplateSyntaxError("Malformed arguments to url tag")
                name, value = match.groups()
                if name:
                    kwargs[name] = parser.compile_filter(value)
                else:
                    args.append(parser.compile_filter(value))

        try:
            return URLNode(viewname, args, kwargs, asvar, legacy_view_name=False)
        except:
            return URLNode(viewname, args, kwargs, asvar)
