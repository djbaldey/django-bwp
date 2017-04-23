# -*- coding: utf-8 -*-
#
#  bwp/contrib/devices/drivers/Zonerich/__init__.py
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
import subprocess

from bwp.contrib.devices.exceptions import DriverError
from bwp.contrib.devices.remote import RemoteCommand


DEFAULT_PORT = '192.168.1.10 9100'
CODE_PAGE = 'cp866'
GS = 0x1D
ESC = 0x1B


class ZonerichError(DriverError):
    pass


class ZonerichIP(object):
    is_remote = False
    port = None

    COMMAND_CUT = '\n' + chr(GS) + chr(0x56) + chr(0x01) + '\n'
    COMMAND_HEADER = '\n' + chr(GS) + chr(0x21) + chr(0x10) + '\n'
    COMMAND_STARDARD = '\n' + chr(GS) + chr(0x21) + chr(0x00) + '\n'
    COMMAND_BELL = '\n' + chr(ESC) + chr(0x39) + chr(0) + chr(0) + chr(64) + '\n'

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote = True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.port = kwargs.get('port', DEFAULT_PORT)

    def _send(self, doc='Текст документа не передан'):
        """ Отправка на печать, ответа не существует. """
        if self.is_remote:
            return self.remote("status", doc=doc)

        text = doc.encode(CODE_PAGE)
        byte_list = [ord(x) for x in text]

        proc = (
            "%(python)s -c 'print bytearray(%(text)s)' | %(ncat)s "
            "--send-only %(port)s"
        )
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
        p.wait()
        return True

    def cut_tape(self, fullcut=True):
        """ Отрез чековой ленты """
        if self.is_remote:
            return self.remote("cut_tape", fullcut=fullcut)

        doc = '' + self.COMMAND_CUT

        if self.status():
            self._send(doc)
            return True

        return False

    def status(self):
        """ Cостояние, по-умолчанию короткое """
        if self.is_remote:
            return self.remote("status")

        try:
            answer = subprocess.check_output([
                "ping", "-c", "1",
                self.port.split(' ')[0]
            ])
        except subprocess.CalledProcessError:
            raise ZonerichError(value=self.port)
        if answer.count('1 received'):
            return True
        return False

    def _prepare_text(self, text):
        """ Удаление лишних символов """
        L = text.split('\n')
        L = [x.strip(' ') for x in L if x]
        text = '\n'.join(L).replace('\n\n', '\n')
        return text + '\n'

    def print_document(self, text='Текст документа не передан', header=''):
        """ Печать предварительного чека или чего-либо другого. """
        if self.is_remote:
            return self.remote("print_document", header=header, text=text)

        doc = ''
        if header:
            doc += self.COMMAND_HEADER + header + '\n'
        doc += (self.COMMAND_STARDARD + self._prepare_text(text) +
                self.COMMAND_CUT + self.COMMAND_BELL)
        if self.status():
            self._send(doc)
            return True  # self.cut_tape()
        raise ZonerichError(value=self.port)


class ZonerichIPDummy(ZonerichIP):

    def __init__(self, remote=False, *args, **kwargs):
        if remote:
            self.is_remote = True
            self.remote = RemoteCommand(*args, **kwargs)
        else:
            self.port = kwargs.get('port', 'DUMMY 9100')

    def _send(self, doc='Текст документа не передан'):
        "Отправка на печать, ответа не существует."
        if self.is_remote:
            return self.remote("status", doc=doc)
        print(doc)
        return True

    def cut_tape(self, fullcut=True):
        "Отрез чековой ленты."
        if self.is_remote:
            return self.remote("cut_tape", fullcut=fullcut)
        if self.status():
            return True
        return False

    def status(self):
        "Cостояние, по-умолчанию короткое."
        if self.is_remote:
            return self.remote("status")
        return True

    def print_document(self, text='Текст документа не передан', header=''):
        """ Печать предварительного чека или чего-либо другого. """
        if self.is_remote:
            return self.remote("print_document", header=header, text=text)

        if self.status():
            if header:
                self._send(header + '\n')
            self._send(self._prepare_text(text))
            return True
        raise ZonerichError(value=self.port)
