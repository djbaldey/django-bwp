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
import subprocess

from bwp.contrib.devices.remote import RemoteCommand

DEFAULT_PORT = '192.168.1.10 9100'
CODE_PAGE = 'cp866'
GS  = 0x1D
ESC = 0x1B

class ZonerichIP(object):
    is_remote = False
    port = None
    
    COMMAND_CUT      = '\n'+chr(GS)+chr(0x56)+chr(0x01)+'\n'
    COMMAND_HEADER   = '\n'+chr(GS)+chr(0x21)+chr(0x10)+'\n'
    COMMAND_STARDARD = '\n'+chr(GS)+chr(0x21)+chr(0x00)+'\n'
    COMMAND_BELL     = '\n'+chr(ESC)+chr(0x39)+chr(0)+chr(0)+chr(64)+'\n'

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote= True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.port = kwargs.get('port', DEFAULT_PORT)

    def _send(self, doc=u'Текст документа не передан'):
        """ Отправка на печать, ответа не существует. """
        if self.is_remote:
            return self.remote("status", short=short)

        # Юникодим "ласково", но принудительно:
        doc = u'' + doc
        text = doc.encode(CODE_PAGE)
        byte_list = [ord(x) for x in text]

        proc = '''%(python)s -c 'print bytearray(%(text)s)' | %(ncat)s --send-only %(port)s'''
        proc = proc % {
            'python': '/usr/bin/python',
            'ncat': '/usr/bin/ncat',
            'text': str(byte_list),
            'port': self.port,
        }

        out = "/dev/null"
        err = "/dev/null"
        p = subprocess.Popen(proc, shell=True,
                stdout=open(out, 'w+b'), 
                stderr=open(err, 'w+b'))
        a = p.wait()
        return True

    def cut_tape(self, fullcut=True):
        """ Отрез чековой ленты """
        if self.is_remote:
            return self.remote("cut_tape", fullcut=fullcut)
        
        doc = u'' + self.COMMAND_CUT

        if self.status():
            self._send(doc)
            return True

        return False

    def status(self):
        """ Cостояние, по-умолчанию короткое """
        if self.is_remote:
            return self.remote("status",)

        answer = subprocess.check_output([
            "ping", "-c", "1",
            self.port.split(' ')[0]
        ])

        if answer.count('1 received'):
            return True

        return False

    def _prepare_text(self, text):
        """ Удаление лишних символов """
        L = text.split('\n')
        L = [x.strip(' ') for x in L if x ]
        text = '\n'.join(L).replace('\n\n', '\n')
        return text + '\n'

    def print_document(self, text=u'Текст документа не передан', header=u''):
        """ Печать предварительного чека или чего-либо другого. """
        if self.is_remote:
            return self.remote("print_document",
                header=header, text=text)

        doc = u''

        if header:
            doc += self.COMMAND_HEADER + header + '\n'

        doc += self.COMMAND_STARDARD + self._prepare_text(text) \
            + self.COMMAND_CUT + self.COMMAND_BELL

        if self.status():
            self._send(doc)
            return True#self.cut_tape()

        raise RuntimeError(unicode(_('Printer is not responding')))
