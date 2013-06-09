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
import datetime

from bwp.contrib.devices.remote import RemoteCommand

from kkt import KKTException, KKT, int2
from protocol import *

class ShtrihFRKDummy(object):
    kkt = None

    def open(self):
        """ Начало работы с ККТ """
        pass

    def status(self, short=True):
        """ Cостояние ККТ, по-умолчанию короткое """
        return 'Dummy state'

    def print_receipt(self, header, summa, comment, buyer, document_type=0, nds=0):
        """ Печать чека """
        pass

    def print_copy(self):
        """ Печать копии последнего документа """
        pass

    def print_continue(self):
        """ Продолжение печати, прерванной из-за сбоя """
        pass

    def print_report(self):
        """ Печать X-отчета """
        pass

    def close_session(self):
        """ Закрытие смены с печатью Z-отчета """
        pass

    def cancel_receipt(self):
        """ Отмена чека """
        pass

    def cancel(self):
        """ Отмена операции """
        pass

    def setup_date(self):
        """ Установка даты как в компьютере """
        pass

    def setup_time(self):
        """ Установка времени как в компьютере """
        pass

    def add_money(self, summa):
        """ Внесение денег в кассу """
        pass

    def get_money(self, summa):
        """ Инкассация """
        pass

    def cut_tape(self):
        """ Обрезка ленты """
        pass

class ShtrihFRK(ShtrihFRKDummy):
    is_remote = False

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote= True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.kkt = KKT(*args, **kwargs)

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
            return self.kkt.x10()
        return self.kkt.x11()

    def print_receipt(self, header, summa, comment, buyer, document_type=0, nds=0):
        """ Печать чека """
        if self.is_remote:
            return self.remote("print_receipt",
                header=header, summa=summa, comment=comment, buyer=bayer,
                document_type=document_type, nds=nds)

        taxes = [0,0,0,0]
        if nds > 0:
            taxes[0] = 2
            # Включаем начисление налогов на ВСЮ операцию чека
            self.kkt.x1E(table=1, row=1, field=17, value=chr(0x1))
            # Включаем печатать налоговые ставки и сумму налога
            self.kkt.x1E(table=1, row=1, field=19, value=chr(0x2))
            self.kkt.x1E(table=6, row=2, field=1, value=int2.pack(nds * 100))

        self.kkt.x8D(document_type) # Открыть чек

        for line in header.split('\n'):
            self.kkt.x17_loop(text=line)

        if document_type == 0:
            _text = u"Принято от %s" % buyer
            self.kkt.x17(text=_text)
            self.kkt.x80(1, summa, text=comment, taxes=taxes)
        else:
            _text = u"Возвращено %s" % buyer
            self.kkt.x17(text=_text)
            self.kkt.x82(1, summa, text=comment, taxes=taxes)

        _text = u"-" * 18
        return self.kkt.x85(summa, text=_text, taxes=taxes)

    def print_copy(self):
        """ Печать копии последнего документа """
        if self.is_remote:
            return self.remote("print_copy")

        return self.kkt.x8C()

    def print_continue(self):
        """ Продолжение печати, прерванной из-за сбоя """
        if self.is_remote:
            return self.remote("print_continue")

        return self.kkt.xB0()

    def print_report(self):
        """ Печать X-отчета """
        if self.is_remote:
            return self.remote("print_report")

        return self.kkt.x40()

    def close_session(self):
        """ Закрытие смены с печатью Z-отчета """
        if self.is_remote:
            return self.remote("close_session")

        return self.kkt.x41()

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
        error = self.kkm.x22(now.year, now.month, now.day)
        if error:
            return error
        return self.kkm.x23(now.year, now.month, now.day)

    def setup_time(self):
        """ Установка времени как в компьютере """
        if self.is_remote:
            return self.remote("setup_time")

        now = datetime.datetime.now()
        return self.kkm.x21(now.hour, now.minute, now.second)

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

    def cut_tape(self):
        """ Обрезка ленты """
        if self.is_remote:
            return self.remote("cut_tape")

        return self.kkt.x25(fullcut=True)
