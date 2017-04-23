#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

# Set name directory of environ
ENV = 'env-django1.4'


def getenv():
    """ Find full path for name directory of environ """
    if ENV:
        thispath = os.path.abspath(os.path.dirname(__file__))
        while thispath:
            j = os.path.abspath(os.path.join(thispath, ENV))
            if thispath == '/' and not os.path.exists(j):
                raise Exception(u'Environ not found')
            if os.path.exists(j):
                return j
            else:
                thispath = os.path.dirname(thispath)
    else:
        return None


if __name__ == "__main__":
    env = getenv()
    if env:
        python = 'python%s.%s' % (str(sys.version_info[0]),
                                  str(sys.version_info[1]))
        packages = os.path.join(env, 'lib', python, 'site-packages')
        sys.path.insert(2, packages)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    from bwp.contrib.devices.models import SpoolerDevice
    from django.utils import timezone
    from datetime import timedelta

    WAITING = SpoolerDevice.STATE_WAITING
    ERROR = SpoolerDevice.STATE_ERROR

    def run(spoolers):
        first = spoolers[0]
        self_sps = spoolers.filter(group_hash=first.group_hash)
        self_sps.update(state=WAITING)
        first.local_device.device
        for s in self_sps:
            method = eval('self.' + s.method)
            kwargs = s.kwargs
            try:
                result = method(**kwargs)
            except Exception:
                self_sps.update(state=ERROR)
                return u'Queued'
        self_sps.all().delete()
        return result

    spoolers = SpoolerDevice.objects.all().order_by('pk')
    now = timezone.now()
    # Зависшие более 1минуты по какой либо причине тоже обрабатываем
    new = now - timedelta(seconds=60)
    # Если есть моложе 1минуты - где-то уже запущен процесс их обработки
    if spoolers.filter(state=WAITING, created__gt=new).count():
        print("Где-то уже запущен процесс обработки")
    elif not spoolers.count():
        print("Пусто")
    else:
        print("Запуск")
        run(spoolers)
