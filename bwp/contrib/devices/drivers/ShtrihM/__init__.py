# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/drivers/ShtrihM/__init__.py
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
import datetime
import time

from django.utils.translation import ugettext as _
from django.utils.encoding import force_bytes

from shtrihmfr.kkt import KKT, KktError, int2
from shtrihmfr.protocol import *  # NOQA

from bwp.contrib.devices.remote import RemoteCommand


SPOOLER_TIMEOUT = 1
SPOOLER_MAX_ATTEMPT = 30


class ShtrihFRK(object):
    SpoolerDevice = None
    local_device = None
    kkt = None
    is_remote = False
    is_open = False

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote = True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.kkt = KKT(*args, **kwargs)

    def get_method_name(self, method):
        if method.im_self == self:
            return method.im_func.func_name
        else:
            return 'kkt.' + method.im_func.func_name

    def make_spooler(self, method, **kwargs):
        if not self.SpoolerDevice:
            return method(**kwargs)

        method = self.get_method_name(method)

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

        method = self.get_method_name(method)

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

        method = self.get_method_name(method)

        spooler = self.SpoolerDevice(
            local_device=self.local_device,
            method=method,
            kwargs=kwargs,
            group_hash=group_hash,
        )
        spooler.save()

        STATE_WAITING = self.SpoolerDevice.STATE_WAITING
        STATE_ERROR = self.SpoolerDevice.STATE_ERROR

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
                raise KktError(_('The device is busy large queue'))
            else:
                self_sps.update(state=STATE_ERROR)
                return 'Queued'
        else:
            result = None
            for s in self_sps.order_by('pk'):
                method = eval('self.' + s.method)
                kwargs = s.kwargs
                try:
                    result = method(**kwargs)
                except Exception as e:
                    if strict:
                        self_sps.all().delete()
                        raise e
                    else:
                        self_sps.update(state=STATE_ERROR)
                        return 'Queued'
            # time.sleep(SPOOLER_TIMEOUT)
            self_sps.all().delete()
            return result

    def open(self):
        """ Начало работы с ККТ """
        if self.is_remote:
            return self.remote("open")

        if not self.is_open:
            kkt_mode = self.kkt.x10()['kkt_mode']
            if kkt_mode == 4:
                self.kkt.xE0()
                time.sleep(5)
            self.is_open = True
        return self.is_open

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
            self.print_continue()  # предварительный вывод неоконченных
        except:
            try:
                self.cancel()  # отмена ошибочных чеков
            except:
                pass
        return True

    def print_document(self, text='Текст документа не передан', header=''):
        """ Печать предварительного чека или чего-либо другого. """
        if self.is_remote:
            return self.remote("print_document", text=text, header=header)
        group_hash = self.make_spooler(self.reset)
        if header:
            for line in header.split('\n'):
                self.append_spooler(group_hash, self.kkt.x12_loop, text=line)
        for line in text.split('\n'):
            self.append_spooler(group_hash, self.kkt.x17_loop, text=line)
        return self.result_spooler(group_hash, self.cut_tape, strict=False)

    def print_receipt(self, specs, cash=0, credit=0, packaging=0, card=0,
                      discount_summa=0, discount_percent=0, document_type=0,
                      nds=0, header='', comment='', buyer='',
                      **kwargs):
        """ Печать чека.
            specs - Это список словарей проданных позиций:
            [
                {
                    'title': 'Хлеб',
                    'price': '10.00',
                    'count': '3',
                    'summa': '30.00',
                    'discount_summa': 1.0,
                },
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
            return self.remote(
                "print_receipt",
                specs=specs, cash=cash, credit=credit,
                packaging=packaging, card=card,
                discount_summa=discount_summa,
                discount_percent=discount_percent,
                document_type=document_type, nds=nds,
                header=header, comment=comment, buyer=buyer,
                **kwargs
            )

        # self.open()
        kkt = self.kkt  # short link

        group_hash = self.make_spooler(self.reset)

        taxes = [0, 0, 0, 0]
        if nds > 0:
            taxes[0] = 2
            # Включаем начисление налогов на ВСЮ операцию чека
            self.append_spooler(
                group_hash, kkt.x1E,
                table=1, row=1, field=17, value=chr(0x1),
            )
            # Включаем печатать налоговые ставки и сумму налога
            self.append_spooler(
                group_hash, kkt.x1E,
                table=1, row=1, field=19, value=chr(0x2),
            )
            self.append_spooler(
                group_hash, kkt.x1E,
                table=6, row=2, field=1, value=int2.pack(nds * 100),
            )

        # Открыть чек
        self.append_spooler(
            group_hash, kkt.x8D,
            document_type=document_type
        )

        if header:
            for line in header.split('\n'):
                self.append_spooler(group_hash, kkt.x17_loop, text=line)

        if document_type == 0:
            text_buyer = 'Принято от %s'
            method = kkt.x80
        elif document_type == 2:
            text_buyer = 'Возвращено %s'
            method = kkt.x82
        elif document_type == 1:
            text_buyer = 'Принято от %s'
            method = kkt.x81
        elif document_type == 3:
            text_buyer = 'Возвращено %s'
            method = kkt.x83
        else:
            raise KktError(_('Type of document must be 0..3'))

        text_buyer = (text_buyer % buyer if buyer else '').strip()

        for spec in specs:
            title = '' + spec['title']
            title = title[:40]
            self.append_spooler(
                group_hash, method,
                count=spec['count'], price=spec['price'],
                text=title, taxes=taxes,
            )
            spec_discount_summa = spec.get('discount_summa', 0)
            if spec_discount_summa:
                line = '{0:>36}'.format('скидка: -%s' % spec_discount_summa)
                self.append_spooler(group_hash, kkt.x17_loop, text=line)

        for line in text_buyer.split('\n'):
            self.append_spooler(group_hash, kkt.x17_loop, text=line)

        for line in comment.split('\n'):
            self.append_spooler(group_hash, kkt.x17_loop, text=line)

        self.append_spooler(group_hash, kkt.x17_loop, text=('=' * 36))

        if discount_summa:
            self.append_spooler(
                group_hash, kkt.x86,
                summa=discount_summa, taxes=taxes,
            )

        summs = [cash, credit, packaging, card]
        return self.result_spooler(
            group_hash, kkt.x85,
            summs=summs, taxes=taxes, discount=discount_percent,
        )

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
        result = self.result_spooler(group_hash, self.kkt.x41)
        # Автоматическая коррекция времени после закрытия смены
        status = self.status(False)
        now = datetime.datetime.now()
        cur = '%s %s' % (status['date'], status['time'])
        try:
            cur = datetime.datetime.strptime(cur, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            diff = now - dt
            if abs(diff.total_seconds()) > 60:
                self.setup_time(now)
                self.setup_date(now)
        return result

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

    def setup_date(self, now=None):
        """ Установка даты как в компьютере """
        if self.is_remote:
            return self.remote("setup_date")
        if not now:
            now = datetime.datetime.now()
        error = self.kkt.x22(now.year, now.month, now.day)
        if error:
            return error
        return self.kkt.x23(now.year, now.month, now.day)

    def setup_time(self, now=None):
        """ Установка времени как в компьютере """
        if self.is_remote:
            return self.remote("setup_time")
        if not now:
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


class ShtrihFRK2(ShtrihFRK):
    "Для онлайн-касс второй версии протокола."
    payments = {}

    def __init__(self, remote=False, *args, **kwargs):
        if not remote:
            if 'payments' in kwargs:
                self.payments = kwargs.pop('payments')
            # Тестируем правильность установки типов оплат
            assert isinstance(self.payments, dict), \
                'Типы оплат должны быть словарём.'
            self.route_payments(0, 0, 0, 0)
        super(ShtrihFRK2, self).__init__(remote, *args, **kwargs)

    def route_payments(self, cash, credit, packaging, card):
        "Возвращает направление типов оплат для закрытия чека."
        payments = [0 for x in range(16)]
        payments[self.payments.get('cash', 0)] = cash
        # Клубная карта клиента (дебетовая)
        payments[self.payments.get('card', 1)] = card
        # Банковская карта
        payments[self.payments.get('credit', 2)] = credit
        # Любая другая форма оплаты
        payments[self.payments.get('packaging', 15)] = packaging
        assert len(payments) == 16, \
            'Количество типов оплат должно быть равно 16.'
        return payments

    def print_receipt(self, specs, cash=0, credit=0, packaging=0, card=0,
                      discount_summa=0, discount_percent=0, document_type=0,
                      nds=0, header='', comment='', buyer='',
                      mail_or_phone='',
                      **kwargs):
        """ Печать чека.
            Новый метод продаж и возвратов для онлайн-касс.

            specs - Это список словарей проданных позиций:
            [
                {
                    'title': 'Хлеб',
                    'price': '10.00',
                    'count': '3',
                    'summa': '30.00',
                    'discount_summa': 1.0,
                },
            ]
            Типы оплат:
                cash      - наличными
                credit    - кредитом
                packaging - тарой
                card      - платёжной картой
            Тип документа:
                0 – продажа -->> (1 – Приход);
                1 – покупка -->> (3 – Расход);
                2 – возврат продажи --> (2 – Возврат прихода);
                3 – возврат покупки --> (4 – Возврат расхода);

        """
        if self.is_remote:
            return self.remote(
                "print_receipt",
                specs=specs, cash=cash, credit=credit,
                packaging=packaging, card=card,
                discount_summa=discount_summa,
                discount_percent=discount_percent,
                document_type=document_type, nds=nds,
                header=header, comment=comment, buyer=buyer,
                mail_or_phone=mail_or_phone,
                **kwargs
            )

        self.open()
        kkt = self.kkt  # short link

        group_hash = self.make_spooler(self.reset)

        taxes = [0, 0, 0, 0]
        if nds > 0:
            taxes[0] = 2
            # Включаем начисление налогов на ВСЮ операцию чека
            # self.append_spooler(
            #     group_hash,
            #     kkt.x1E, table=1, row=1, field=17, value=chr(0x1),
            # )
            # Включаем печатать налоговые ставки и сумму налога
            # self.append_spooler(
            #     group_hash,
            #     kkt.x1E, table=1, row=1, field=19, value=chr(0x2),
            # )
            # self.append_spooler(
            #     group_hash,
            #     kkt.x1E, table=6, row=2, field=1,
            #     value=int2.pack(nds * 100),
            # )

        # Открыть чек
        # self.append_spooler(
        #     group_hash, kkt.x8D, document_type=document_type
        # )

        if header:
            for line in header.split('\n'):
                self.append_spooler(group_hash, kkt.x17_loop, text=line)

        if document_type == 0:
            text_buyer = 'Приход от %s'
            operation = 1
        elif document_type == 2:
            text_buyer = 'Возврат прихода %s'
            operation = 2
        elif document_type == 1:
            text_buyer = 'Расход к %s'
            operation = 3
        elif document_type == 3:
            text_buyer = 'Возврат расхода %s'
            operation = 4
        else:
            raise KktError(_('Type of document must be 0..3'))

        text_buyer = (text_buyer % buyer if buyer else '').strip()

        total_summa = 0
        total_discount = 0

        for spec in specs:
            text = spec['title']
            barcode = spec.get('barcode') or 0
            if barcode and not isinstance(barcode, int):
                try:
                    barcode = int(barcode)
                except ValueError:
                    barcode = 0
            count = int(spec['count'])
            price = round(float(spec['price']), 2)
            src_summ = count * price
            discount = round(float(spec.get('discount_summa', 0)), 2)
            if discount:
                price -= round(1.0 * discount / count, 2)
            new_summ = count * price
            total_summa += new_summ
            # Пересчитываем скидку для того чтобы вывести правильные
            # копейки
            discount = src_summ - new_summ
            total_discount += discount

            self.append_spooler(
                group_hash,
                kkt.xFF0D,
                operation=operation,
                count=count,
                price=price,
                discount=0,
                increment=0,
                department=0,
                tax=0,
                barcode=barcode,
                text=text,
            )
            if discount:
                line = '{0:>36}'.format('включая скидку: %.2f' % discount)
                self.append_spooler(group_hash, kkt.x17_loop, text=line)

        if mail_or_phone:
            text_buyer += ' (%s)' % mail_or_phone
            # Передача TLV для ОФД
            self.append_spooler(
                group_hash,
                kkt.xFF0C,
                tlv_dict={1008: mail_or_phone},
            )

        if text_buyer:
            for line in text_buyer.split('\n'):
                self.append_spooler(group_hash, kkt.x17_loop, text=line)
        if comment:
            for line in comment.split('\n'):
                self.append_spooler(group_hash, kkt.x17_loop, text=line)

        if total_discount:
            self.append_spooler(group_hash, kkt.x17_loop, text='-' * 36)
            line = '{0:>36}'.format('общая скидка: %.2f' % total_discount)
            self.append_spooler(group_hash, kkt.x17_loop, text=line)
        self.append_spooler(group_hash, kkt.x17_loop, text=('=' * 36))

        assert total_summa <= cash + credit + packaging + card, force_bytes(
            'Сумма спецификаций больше, чем сумма типов оплат: '
            '%.2f != %.2f' % (total_summa, cash + credit + packaging + card)
        )

        payments = self.route_payments(cash, credit, packaging, card)

        return self.result_spooler(
            group_hash,
            kkt.x8E,
            payments=payments,
            taxes=taxes,
            discount_percent=0,  # Очень важно теперь ничего не передавать!
        )


def run_tests(version=1, port='/dev/ttyUSB0', bod=115200):
    if version == 1:
        DevClass = ShtrihFRK
    elif version == 2:
        DevClass = ShtrihFRK2
    dev = DevClass(port=port, bod=bod)
    print('status:')
    status = dev.status()
    print(status)
    if status['kkt_mode'] == 4:
        print('setup_date:')
        print(dev.setup_date())
        print('setup_time:')
        print(dev.setup_time())
    # print('print_document:')
    # header = 'Заголовок документа'
    # text = (
    #     'Текст документа с переводом первой строки и большой второй строкой:\n'
    #     'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '
    #     'eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim '
    #     'ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut '
    #     'aliquip ex ea commodo consequat. Duis aute irure dolor in '
    #     'reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla '
    #     'pariatur. Excepteur sint occaecat cupidatat non proident, sunt in '
    #     'culpa qui officia deserunt mollit anim id est laborum.'
    #     ' \n \n \n \n \n \n \n \n \n \n'
    # )
    # print(dev.print_document(text=text, header=header))

    specs = [
        {
            'title': 'Хлеб чёрный Бородинский',
            'price': '30.00',
            'count': '2',
            'summa': '60.00',
            'discount_summa': '1.00',
        },
        {
            'title': 'Молоко',
            'price': '54.00',
            'count': '3',
            'summa': '162.00',
            'discount_summa': 4.50,
        },
        {
            'title': 'Водка Беленькая',
            'price': '390.00',
            'count': '2',
            'summa': '780.00',
            'discount_summa': 30.0,
            'barcode': 999999999999,
        },
    ]
    summa = 60 - 1 + 162 - 4.50 + 780 - 30
    cash = summa
    card = summa / 3
    credit = summa / 3
    packaging = 0
    header = 'Продажа товаров'
    comment = 'Комментарий к продаже товаров'
    buyer = 'Иван Иванов'
    mail_or_phone = '89997776655'

    print('print_receipt:')
    print(dev.print_receipt(
        specs, cash=cash, credit=credit, packaging=packaging, card=card,
        discount_summa=0, discount_percent=0, document_type=0, nds=0,
        header=header, comment=comment, buyer=buyer,
        mail_or_phone=mail_or_phone
    ))

    # time.sleep(10)
    # print(dev.print_copy())
    # time.sleep(10)
    # print(dev.print_report())
    # time.sleep(10)
    # print(dev.close_session())
