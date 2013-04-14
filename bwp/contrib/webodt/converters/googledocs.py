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
import urllib, urllib2, uuid
from lxml import etree
from cStringIO import StringIO
from bwp.contrib.webodt import Document
from bwp.contrib.webodt.converters import ODFConverter

from bwp.contrib.webodt.conf import WEBODT_GOOGLEDOCS_EMAIL, WEBODT_GOOGLEDOCS_PASSWORD

AUTH_URL = 'https://www.google.com/accounts/ClientLogin'


class DeleteRequest(urllib2.Request):
    def get_method(self):
        return 'DELETE'


class GoogleDocsODFConverter(ODFConverter):


    def _get_auth_token(self):
        post_data = {
            'accountType': 'HOSTED_OR_GOOGLE',
            'Email': WEBODT_GOOGLEDOCS_EMAIL,
            'Passwd': WEBODT_GOOGLEDOCS_PASSWORD,
            'service': 'writely', # http://code.google.com/intl/ru/apis/documents/faq_gdata.html#clientlogin
            'source': 'NetAngels-webodt-0.1',
        }
        url = urllib2.urlopen(AUTH_URL, urllib.urlencode(post_data))
        data = url.read()
        data_dict = dict([line.split('=', 1) for line in data.splitlines()])
        return data_dict['Auth']


    def __init__(self):
        self.auth_token = self._get_auth_token()


    def convert(self, document, format=None, output_filename=None, delete_on_close=True):
        # opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=1))
        # urllib2.urlopen = opener.open
        output_filename, format = self._guess_format_and_filename(output_filename, format)
        # upload document
        url = 'https://docs.google.com/feeds/default/private/full'
        data = document.read()
        headers = {
            'GData-Version': '3.0',
            'Authorization': 'GoogleLogin auth=%s' % self.auth_token,
            'Content-Length': str(len(data)),
            'Content-Type': document.content_type,
            'Slug': '%s.%s' % (uuid.uuid4(), document.format),
        }
        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)
        data = response.read()
        response.close()
        tree = etree.parse(StringIO(data))
        # get document resource id
        resource_id = tree.xpath('gd:resourceId/text()', namespaces={'gd': 'http://schemas.google.com/g/2005'})
        if len(resource_id) != 1:
            raise ValueError('Unexpected error. Document schema was changed')
        resource_id = resource_id[0]
        # get document URL
        document_url = tree.xpath('atom:content/@src', namespaces={'atom': 'http://www.w3.org/2005/Atom'})
        if len(document_url) != 1:
            raise ValueError('Unexpected error. Document schema was changed')
        document_url = document_url[0]
        url = document_url + '&exportFormat=%(format)s&format=%(format)s' % {'format': format}
        # download document
        headers = {
            'GData-Version': '3.0',
            'Authorization': 'GoogleLogin auth=%s' % self.auth_token,
        }
        request = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(request)
        data = response.read()
        response.close()
        fd = open(output_filename, 'w')
        fd.write(data)
        fd.close()

        # remove document from google docs
        self._remove_document(resource_id)

        # return document
        fd = Document(output_filename, mode='r', delete_on_close=delete_on_close)
        return fd

    def _remove_document(self, resource_id):
        # remove document from google docs
        url = 'https://docs.google.com/feeds/default/private/full/%s?delete=true' % resource_id
        headers = {
            'GData-Version': '3.0',
            'If-Match': '*',
            'Authorization': 'GoogleLogin auth=%s' % self.auth_token,
        }
        request = DeleteRequest(url, None, headers)
        response = urllib2.urlopen(request)
        data = response.read()
        response.close()
