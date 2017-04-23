# coding: utf-8
"""
Management utility for spooler device.
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.encoding import force_text

from bwp.contrib.devices.models import SpoolerDevice


def deep_getattr(obj, name):
    attr = obj
    for a in name.split('.'):
        attr = getattr(attr, a)
    return attr


class Command(BaseCommand):

    help = 'Used to runs process of spooler device.'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        WAITING = SpoolerDevice.STATE_WAITING
        ERROR = SpoolerDevice.STATE_ERROR

        spoolers = SpoolerDevice.objects.all().order_by('pk')
        now = timezone.now()
        # Зависшие более 1минуты по какой либо причине тоже обрабатываем
        new = now - timezone.timedelta(seconds=60)
        # Если есть моложе 1минуты - где-то уже запущен процесс их обработки
        if spoolers.filter(state=WAITING, created__gt=new).count():
            self.stderr.write('Где-то уже запущен процесс обработки')
        elif not spoolers.count():
            if verbosity > 1:
                self.stdout.write('Пусто\n')
        else:
            self.stdout.write('Запуск\n')
            first = spoolers[0]
            queue = spoolers.filter(group_hash=first.group_hash)
            queue.update(state=WAITING)
            dev = first.local_device.device
            for s in queue:
                method = deep_getattr(dev, s.method)
                kwargs = s.kwargs
                try:
                    method(**kwargs)
                except Exception as e:
                    queue.update(state=ERROR)
                    self.stderr.write('Ошибка')
                    if verbosity > 1:
                        self.stderr.write(force_text(e))
                    return
            queue.all().delete()
