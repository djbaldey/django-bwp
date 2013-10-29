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
from django.utils.translation import ugettext_lazy as _
import datetime, time

from bwp.contrib.devices.remote import RemoteCommand

from kkt import KKT, int2
from protocol import *

SPOOLER_TIMEOUT = 1
SPOOLER_MAX_ATTEMPT = 30

class ShtrihFRK(object):
    SpoolerDevice      = None
    local_device = None
    kkt       = None
    is_remote = False

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote= True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.kkt = KKT(*args, **kwargs)

    def make_spooler(self, method, **kwargs):
        if not self.SpoolerDevice:
            return method(**kwargs)
        if method.im_self == self:
            method = method.im_func.func_name
        else:
            method = 'kkt.'+ method.im_func.func_name

        spooler = self.SpoolerDevice(
            local_device=self.local_device,
            method=method,
            kwargs=kwargs,
        )
        spooler.save()

        return spooler.group_hash

    def append_spooler(self, group_hash, method, **kwargs):
        if not self.SpoolerDevice:
            return method(**kwargs)
        if method.im_self == self:
            method = method.im_func.func_name
        else:
            method = 'kkt.'+ method.im_func.func_name

        spooler = self.SpoolerDevice(
            local_device=self.local_device,
            method=method,
            kwargs=kwargs,
            group_hash=group_hash,
        )
        spooler.save()
        return spooler.group_hash

    def result_spooler(self, group_hash, method, strict=True, **kwargs):
        if not self.SpoolerDevice:
            return method(**kwargs)
        if method.im_self == self:
            method = method.im_func.func_name
        else:
            method = 'kkt.'+ method.im_func.func_name

        spooler = self.SpoolerDevice(
            local_device=self.local_device,
            method=method,
            kwargs=kwargs,
            group_hash=group_hash,
        )
        spooler.save()

        STATE_WAITING = self.SpoolerDevice.STATE_WAITING
        STATE_ERROR   = self.SpoolerDevice.STATE_ERROR

        all_sps = self.SpoolerDevice.objects.filter(
                local_device=self.local_device, state=STATE_WAITING
                ).order_by('pk')
        self_sps = all_sps.filter(group_hash=spooler.group_hash)
        min_pk = self_sps[0].pk

        other_sps = all_sps.exclude(group_hash=spooler.group_hash)
        c = other_sps.count()
        o = other_sps[0].pk < min_pk if c else False
        n = 0
        while c and o and n < SPOOLER_MAX_ATTEMPT:
            time.sleep(SPOOLER_TIMEOUT)
            n += 1
            other_sps = all_sps.exclude(group_hash=spooler.group_hash)
            c = other_sps.count()
            o = other_sps[0].pk < min_pk if c else False

        if c and o:
            if strict:
                self_sps.all().delete()
                raise RuntimeError(unicode(_('The device is busy large queue')))
            else:
                self_sps.update(state=STATE_ERROR)
                return u'Queued'
        else:
            result = None
            for s in self_sps.order_by('pk'):
                method = eval('self.'+ s.method)
                kwargs = s.kwargs
                try:
                    result = method(**kwargs)
                except Exception as e:
                    if strict:
                        self_sps.all().delete()
                        raise e
                    else:
                        self_sps.update(state=STATE_ERROR)
                        return u'Queued'
            #~ time.sleep(SPOOLER_TIMEOUT)
            self_sps.all().delete()
            return result

    def open(self):
        """ Начало работы с ККТ """
        if self.is_remote:
            return self.remote("open")

        return True

    def status(self, short=True):
        """ Cостояние ККТ, по-умолчанию короткое """
        if self.is_remote:
            return self.remote("status", short=short)

        if short:
            return self.result_spooler(None, self.kkt.x10)
        return self.result_spooler(None, self.kkt.x11)

    def reset(self):
        """ Сброс предыдущей ошибки или остановки печати """
        try:
            self.print_continue() # предварительный вывод неоконченных
        except:
            try:
                self.cancel() # отмена ошибочных чеков
            except:
                pass
        return True

    def print_document(self, text=u'Текст документа не передан', header=u''):
        """ Печать предварительного чека или чего-либо другого. """
        if self.is_remote:
            return self.remote("print_document",
                header=header, text=text)

        group_hash = self.make_spooler(self.reset)

        if header:
            for line in header.split('\n'):
                self.append_spooler(group_hash, self.kkt.x12_loop, text=line)

        for line in text.split('\n'):
            self.append_spooler(group_hash, self.kkt.x17_loop, text=line)

        return self.result_spooler(group_hash, self.cut_tape, strict=False)

    def print_receipt(self, specs, cash=0, credit=0, packaging=0, card=0,
    discount_summa=0, discount_percent=0, document_type=0, nds=0,
    header=u'', comment=u'', buyer=u''):
        """ Печать чека.
            specs - Это список словарей проданных позиций:
                [{'title':u'Хлеб',
                 'price':'10.00', 'count':u'3', 'summa':'30.00'},
                 {'title':u'',
                 'price':'10.00', 'count':u'3', 'summa':'30.00'},
                ]
            Типы оплат:
                cash      - наличными
                credit    - кредитом
                packaging - тарой
                card      - платёжной картой
            Тип документа:
                0 – продажа;
                1 – покупка;
                2 – возврат продажи;
                3 – возврат покупки

        """
        if self.is_remote:
            return self.remote("print_receipt",
                specs=specs, cash=cash, credit=credit,
                packaging=packaging, card=card,
                discount_summa=discount_summa, discount_percent=discount_percent,
                document_type=document_type, nds=nds,
                header=header, comment=comment, buyer=buyer,
            )

        group_hash = self.make_spooler(self.reset)

        taxes = [0,0,0,0]
        if nds > 0:
            taxes[0] = 2
            # Включаем начисление налогов на ВСЮ операцию чека
            self.append_spooler(group_hash,
                self.kkt.x1E, table=1, row=1, field=17, value=chr(0x1))
            # Включаем печатать налоговые ставки и сумму налога
            self.append_spooler(group_hash,
                self.kkt.x1E, table=1, row=1, field=19, value=chr(0x2))
            self.append_spooler(group_hash,
                self.kkt.x1E, table=6, row=2, field=1, value=int2.pack(nds * 100))

        self.append_spooler(group_hash,
            self.kkt.x8D, document_type=document_type) # Открыть чек

        for line in header.split('\n'):
            self.append_spooler(group_hash, self.kkt.x17_loop, text=line)

        if document_type == 0:
            text_buyer = u"Принято от %s"
            method = self.kkt.x80
        elif document_type == 1:
            text_buyer = u"Принято от %s"
            method = self.kkt.x81

        elif document_type == 2:
            text_buyer = u"Возвращено %s"
            method = self.kkt.x82

        elif document_type == 3:
            text_buyer = u"Возвращено %s"
            method = self.kkt.x83
        else:
            raise RuntimeError(unicode(_('Type of document must be 0..3')))

        text_buyer = text_buyer % buyer if buyer else u''

        for spec in specs:
            title = u''+spec['title']
            title = title[:40]
            self.append_spooler(group_hash,
                method, count=spec['count'], price=spec['price'],
                                        text=title, taxes=taxes)
            spec_discount_summa = spec.get('discount_summa', 0)
            if spec_discount_summa:
                line = u'{0:>36}'.format(u'скидка: -%s' % spec_discount_summa)
                self.append_spooler(group_hash,
                    self.kkt.x17_loop, text=line)

        for line in text_buyer.split('\n'):
            self.append_spooler(group_hash, self.kkt.x17_loop, text=line)

        for line in comment.split('\n'):
            self.append_spooler(group_hash, self.kkt.x17_loop, text=line)
        
        self.append_spooler(group_hash, self.kkt.x17_loop, text=u'='*36)
        
        if discount_summa:
            self.append_spooler(group_hash,
                self.kkt.x86, summa=discount_summa, taxes=taxes)

        _text = u"-" * 18
        summs = [cash,credit,packaging,card]
        return self.result_spooler(group_hash,
            self.kkt.x85, summs=summs, taxes=taxes, discount=discount_percent)

    def print_copy(self):
        """ Печать копии последнего документа """
        if self.is_remote:
            return self.remote("print_copy")

        group_hash = self.make_spooler(self.reset)

        return self.result_spooler(group_hash, self.kkt.x8C)

    def print_continue(self):
        """ Продолжение печати, прерванной из-за сбоя """
        if self.is_remote:
            return self.remote("print_continue")

        return self.kkt.xB0()

    def print_report(self):
        """ Печать X-отчета """
        if self.is_remote:
            return self.remote("print_report")

        group_hash = self.make_spooler(self.reset)

        return self.result_spooler(group_hash, self.kkt.x40)

    def close_session(self):
        """ Закрытие смены с печатью Z-отчета """
        if self.is_remote:
            return self.remote("close_session")

        group_hash = self.make_spooler(self.reset)

        return self.result_spooler(group_hash, self.kkt.x41)

    def cancel_receipt(self):
        """ Отмена чека """
        if self.is_remote:
            return self.remote("cancel_receipt")

        return self.kkt.x88()

    def cancel(self):
        """ Отмена операции """
        if self.is_remote:
            return self.remote("cancel")

        return self.cancel_receipt()

    def setup_date(self):
        """ Установка даты как в компьютере """
        if self.is_remote:
            return self.remote("setup_date")

        now = datetime.datetime.now() 
        error = self.kkt.x22(now.year, now.month, now.day)
        if error:
            return error
        return self.kkt.x23(now.year, now.month, now.day)

    def setup_time(self):
        """ Установка времени как в компьютере """
        if self.is_remote:
            return self.remote("setup_time")

        now = datetime.datetime.now()
        return self.kkt.x21(now.hour, now.minute, now.second)

    def add_money(self, summa):
        """ Внесение денег в кассу """
        if self.is_remote:
            return self.remote("add_money", summa=summa)

        return self.kkt.x50(summa)

    def get_money(self, summa):
        """ Инкассация """
        if self.is_remote:
            return self.remote("get_money", summa=summa)

        return self.kkt.x51(summa)

    def cut_tape(self, fullcut=True):
        """ Отрез чековой ленты """
        if self.is_remote:
            return self.remote("cut_tape", fullcut=fullcut)

        return self.kkt.x25(fullcut=fullcut)
