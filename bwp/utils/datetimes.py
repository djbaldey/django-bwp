# -*- coding: utf-8 -*-
#
#  bwp/utils/datetimes.py
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
from django.utils import timezone
from django.utils.dateparse import parse_datetime


def datetime_round(dt=None, minute=True, hour=False, day=False):
    """
    Округление времени до секунды, минуты, часа или дня.
    По умолчанию до минуты.
        до дня:     rounded(day=True)
        до часа:    rounded(hour=True)
        до минуты:  rounded()
        до секунды: rounded(minute=False)

    Если нужно округлить заданное время,то оно передаётся в
    параметре `dt`.

    На вход можно подавать как naive, так и aware, результатом будет
    аналогичное.
    Если генерируется новое время, то результатом будет naive при
    settings.USE_TZ = False, иначе - aware.
    """
    if not isinstance(dt, timezone.datetime):
        dt = timezone.now()

    dt = dt.replace(microsecond=0)

    if day:
        dt = dt.replace(hour=0, minute=0, second=0)
    elif hour:
        dt = dt.replace(minute=0, second=0)
    elif minute:
        dt = dt.replace(second=0)

    return dt


# Deprecated:
dt_rounded = datetime_round


def datetime_local(value=None):
    """
    Переводит значение в текущую зону локального времени.
    На вход можно подавать как naive, так и aware, результатом будет
    аналогичное.
    Если генерируется новое время, то результатом будет naive при
    settings.USE_TZ = False, иначе - aware.
    """
    if not value:
        value = timezone.now()
    return timezone.localtime(value, True)


def datetime_server(value=None):
    """
    Переводит значение в зону серверного времени.
    На вход можно подавать как naive, так и aware, результатом будет
    аналогичное.
    Если генерируется новое время, то результатом будет naive при
    settings.USE_TZ = False, иначе - aware.
    """
    if not value:
        value = timezone.now()

    if timezone.is_naive(value):
        return value

    tz_curr = timezone.get_current_timezone()
    tz_serv = timezone.get_default_timezone()

    if tz_curr != tz_serv:
        timezone.activate(tz_serv)
        value = timezone.localtime(value, tz_serv)
        timezone.activate(tz_curr)
    else:
        value = timezone.localtime(value, tz_curr)

    return value


def datetime_naive(value=None):
    """
    Переводит значение в текущую зону локального времени.
    Возвращает простое время.
    """
    return datetime_local(value).replace(tzinfo=None)


def datetime_aware(value=None):
    """
    Переводит значение (даже простое) в текущую зону локального времени.
    Возвращает aware c текущей временной зоной.
    """
    return datetime_local(value).replace(tzinfo=timezone.get_current_timezone())


def datetime_server_naive(value=None):
    """
    Переводит значение в зону серверного времени settings.TIME_ZONE.
    Возвращает простое время.
    """
    return datetime_server(value).replace(tzinfo=None)


def datetime_server_aware(value=None):
    """
    Переводит значение (даже простое) в зону серверного времени.
    Возвращает aware c временной зоной сервера.
    """
    return datetime_server(value).replace(tzinfo=timezone.get_default_timezone())


def current_date():
    """
    Возвращает текущую дату локальной зоны.
    """
    return datetime_naive().date()


def current_time():
    """
    Возвращает текущее время локальной зоны.
    """
    return datetime_naive().time()


def server_date():
    """
    Возвращает текущую дату сервера по settings.TIME_ZONE.
    """
    return datetime_server_naive().date()


def server_time():
    """
    Возвращает текущее время сервера по settings.TIME_ZONE.
    """
    return datetime_server_naive().time()


def parse_datetime_to_naive(value):
    """
    Парсер строкового значения (naive или aware) в локальное naive.
    """
    value = parse_datetime(value)
    if value:
        return datetime_naive(value)
    return None


def parse_datetime_to_aware(value):
    """
    Парсер строкового значения (naive или aware) в локальное aware.
    """
    value = parse_datetime(value)
    if value:
        return datetime_aware(value)
    return None


def parse_datetime_to_server_naive(value):
    """
    Парсер строкового значения (naive или aware) в серверное naive.
    """
    value = parse_datetime(value)
    if value:
        return datetime_server_naive(value)
    return None


def parse_datetime_to_server_aware(value):
    """
    Парсер строкового значения (naive или aware) в серверное aware.
    """
    value = parse_datetime(value)
    if value:
        return datetime_server_aware(value)
    return None
