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

Whereas Django Templates accept string as template source, there is
inconvenient way of working with ODF template, because ODF work with a
relatively complex structure and it's easier to pass just template_name.

ODFTemplate accepts both packed (regular) or unpacked .odt documents as
templates. Unpacked ODFTemplate is nothing more than just unzipped .odt file.
"""
import os
import zipfile
import tempfile
import shutil
import time
from django.template import Template
from django.utils.encoding import smart_str
from bwp.contrib.webodt.conf import WEBODT_TEMPLATE_PATH, WEBODT_ODF_TEMPLATE_PREPROCESSORS, WEBODT_TMP_DIR
from bwp.contrib.webodt.preprocessors import list_preprocessors


class HTMLTemplate(object):
    """ HTML template class """
    format = 'html'
    content_type = 'text/html'

    def __init__(self, template_name):
        """ Create object by the template name or full path.
            The template name is relative to ``WEBODT_TEMPLATE_PATH``
            directory.
        """
        if os.path.isfile(os.path.abspath(template_name)):
            self.template_name = os.path.basename(template_name)
            self.template_path = os.path.abspath(template_name)
        else:
            self.template_name = template_name
            self.template_path = os.path.join(WEBODT_TEMPLATE_PATH, template_name)
            if not os.path.isfile(self.template_path):
                raise ValueError('Template %s not found in directory %s' % (self.template_name, WEBODT_TEMPLATE_PATH))

    def get_content(self):
        fd = open(self.template_path, 'r')
        content = fd.read()
        fd.close()
        return content

    def render(self, context, delete_on_close=True):
        """ Return rendered HTML (webodt.HTMLDocument instance) """
        # get rendered content
        template = Template(self.get_content())
        content = template.render(context)
        # create and return .html file
        _, tmpfile = tempfile.mkstemp(suffix='.html', dir=WEBODT_TMP_DIR)
        fd = open(tmpfile, 'w')
        fd.write(smart_str(content))
        fd.close()
        # return HTML document
        return HTMLDocument(tmpfile, delete_on_close=delete_on_close)


class ODFTemplate(object):
    """
    ODF template class
    """

    format = 'odt'
    content_type = 'application/vnd.oasis.opendocument.text'
    _fake_timestamp = time.mktime((2010,1,1,0,0,0,0,0,0))

    def __init__(self, template_name, preprocessors=None):
        """ Create object by the template name or full path.
            The template name is relative to ``WEBODT_TEMPLATE_PATH``
            directory.

            template_name: name of the template to load and handle
        """
        if not preprocessors:
            preprocessors = WEBODT_ODF_TEMPLATE_PREPROCESSORS
        self.preprocessors = preprocessors
        if os.path.isfile(os.path.abspath(template_name)):
            self.template_name = os.path.basename(template_name)
            self.template_path = os.path.abspath(template_name)
        else:
            self.template_name = template_name
            self.template_path = os.path.join(WEBODT_TEMPLATE_PATH, template_name)
        if os.path.isfile(self.template_path):
            self.packed = True
            self.handler = _PackedODFHandler(self.template_path)
        elif os.path.isdir(self.template_path):
            self.packed = False
            self.handler = _UnpackedODFHandler(self.template_path)
        else:
            raise ValueError('Template %s not found in directory %s' % (self.template_name, WEBODT_TEMPLATE_PATH))

    def get_content_xml(self):
        """ Return the content.xml file contents """
        return self.handler.get_content_xml()

    def render(self, context, delete_on_close=True):
        """ Return rendered ODF (webodt.ODFDocument instance)"""
        # create temp output directory
        tmpdir = tempfile.mkdtemp()
        self.handler.unpack(tmpdir)
        # store updated content.xml
        template_content = self.get_content_xml()
        for preprocess_func in list_preprocessors(self.preprocessors):
            template_content = preprocess_func(template_content)
        template = Template(template_content)
        content_xml = template.render(context)
        content_filename = os.path.join(tmpdir, 'content.xml')
        content_fd = open(content_filename, 'w')
        content_fd.write(smart_str(content_xml))
        content_fd.close()
        # create .odt file
        _, tmpfile = tempfile.mkstemp(suffix='.odt', dir=WEBODT_TMP_DIR)
        tmpzipfile = zipfile.ZipFile(tmpfile, 'w')
        for root, _, files in os.walk(tmpdir):
            for fn in files:
                path = os.path.join(root, fn)
                os.utime(path, (self._fake_timestamp, self._fake_timestamp))
                fn = os.path.relpath(path, tmpdir)
                tmpzipfile.write(path, fn)
        tmpzipfile.close()
        # remove directory tree
        shutil.rmtree(tmpdir)
        # return ODF document
        return ODFDocument(tmpfile, delete_on_close=delete_on_close)


class _PackedODFHandler(object):

    def __init__(self, filename):
        self.filename = filename

    def get_content_xml(self):
        fd = zipfile.ZipFile(self.filename)
        data = fd.read('content.xml')
        fd.close()
        return data

    def unpack(self, dstdir):
        fd = zipfile.ZipFile(self.filename)
        fd.extractall(path=dstdir)
        fd.close()


class _UnpackedODFHandler(object):

    def __init__(self, dirname):
        self.dirname = dirname

    def get_content_xml(self):
        fd = open(os.path.join(self.dirname, 'content.xml'), 'r')
        data = fd.read()
        fd.close()
        return data

    def unpack(self, dstdir):
        os.rmdir(dstdir)
        shutil.copytree(self.dirname, dstdir)


class Document(file):

    def __init__(self, filename, mode='rb', buffering=1, delete_on_close=True):
        file.__init__(self, filename, mode, buffering)
        self.delete_on_close = delete_on_close

    def delete(self):
        os.unlink(self.name)

    def close(self):
        file.close(self)
        if self.delete_on_close:
            self.delete()


class HTMLDocument(Document):
    format = 'html'
    content_type = 'text/html'

    def get_content(self):
        fd = open(self.name, 'r')
        content = fd.read()
        fd.close()
        return content


class ODFDocument(Document):
    format = 'odt'
    content_type = 'application/vnd.oasis.opendocument.text'

    def get_content_xml(self):
        fd = zipfile.ZipFile(self.name)
        data = fd.read('content.xml')
        fd.close()
        return data
