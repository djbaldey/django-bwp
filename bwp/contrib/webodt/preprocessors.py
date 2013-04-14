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
from django.utils.importlib import import_module
from cStringIO import StringIO
from lxml import etree
import re


def list_preprocessors(preprocessors):
    """Create and return list of preprocessor functions
    On a basis parameters:
        `preprocessors` - list of preprocessor function names
    """
    ret = []
    for preprocessor in preprocessors:
        module_name, class_name = preprocessor.rsplit('.', 1)
        mod = import_module(module_name)
        preprocessor_func = getattr(mod, class_name)
        ret.append(preprocessor_func)
    return ret


def unescape_templatetags_preprocessor(template_content):
    replace_map = [
        ('&quot;', '"'),
        ('&lt;', '<'),
        ('&gt;', '>'),
        ('&amp;', '&'),
    ]
    for from_sym, to_sym in replace_map:
        for include_text in re.findall(r'{%(.+?)%}', template_content):
            new_include_text = include_text.replace(from_sym, to_sym)
            template_content = template_content.replace(
                '{%%%s%%}' % include_text, '{%%%s%%}' % new_include_text
            )
        for include_text in re.findall(r'{{(.+?)}}', template_content):
            new_include_text = include_text.replace(from_sym, to_sym)
            template_content = template_content.replace(
                '{{%s}}' % include_text, '{{%s}}' % new_include_text
            )
    return template_content

def xmlfor_preprocessor(template_content):
    tree = etree.parse(StringIO(template_content))

    # 1. search for xmlfor pairs
    re_xmlfor = re.compile(r'{%\s*xmlfor([^%]*)%}')
    re_endxmlfor = re.compile(r'{%\s*endxmlfor[^%]*%}')
    xmlfor_pairs = []
    xmlfor_starts = []
    for el in tree.iter():
        # search for start tag in text
        re_xmlfor_match = re_xmlfor.search(el.text) if el.text else None
        if re_xmlfor_match:
            forloop_clause = re_xmlfor_match.group(1)
            xmlfor_starts.append((el, forloop_clause)) # (<div ...>, 'person in people')
            el.text = re_xmlfor.sub('', el.text)
        # search for start tag in tail
        re_xmlfor_match = re_xmlfor.search(el.tail) if el.tail else None
        if re_xmlfor_match:
            forloop_clause = re_xmlfor_match.group(1)
            xmlfor_starts.append((el.getparent(), forloop_clause))
            el.tail = re_xmlfor.sub('', el.tail)
        # search for end tag in text
        re_endxmlfor_match = re_endxmlfor.search(el.text) if el.text else None
        if re_endxmlfor_match:
            try:
                start_el, forloop_clause = xmlfor_starts.pop()
            except IndexError, e:
                raise ValueError('Unexpected {%% endxmlfor %%} tag near %s' % el.text)
            xmlfor_pairs.append((start_el, el, forloop_clause))
            el.text = re_endxmlfor.sub('', el.text)
        # search for end tag in tail
        re_endxmlfor_match = re_endxmlfor.search(el.tail) if el.tail else None
        if re_endxmlfor_match:
            try:
                start_el, forloop_clause = xmlfor_starts.pop()
            except IndexError, e:
                raise ValueError('Unexpected {%% endxmlfor %%} tag near %s' % el.tail)
            xmlfor_pairs.append((start_el, el.getparent(), forloop_clause))
            el.tail = re_endxmlfor.sub('', el.tail)

    if xmlfor_starts:
        raise ValueError('Unclosed {%% xmlfor %%} tag near %s' % xmlfor_starts[0][0].text)

    # 2. for each pair create {% for %} loop around common ancestor
    for start_tag, end_tag, forloop_clause in xmlfor_pairs:
        ancestor_tag = _find_common_ancestor(start_tag, end_tag)

        # before
        for_text = u'{%% for%s%%}' % forloop_clause
        prev_tag = ancestor_tag.getprevious()
        if prev_tag is not None:
            prev_tail = prev_tag.tail or ''
            prev_tag.tail = u'%s%s' % (prev_tail, for_text)
        else:
            parent_tag = ancestor_tag.getparent()
            parent_text = parent_tag.text or ''
            parent_tag.text = u'%s%s' % (parent_text, for_text)

        # after
        ancestor_tail = ancestor_tag.tail or ''
        ancestor_tag.tail = u'%s%s' % (u'{% endfor %}', ancestor_tail)
    return _tree_to_string(tree)

def _find_common_ancestor(tag1, tag2):
    for ancestor in tag1.iterancestors():
        if ancestor in tag2.iterancestors():
            return ancestor

def _tree_to_string(tree):
    output = StringIO()
    tree.write(output)
    output.seek(0)
    return output.read()
