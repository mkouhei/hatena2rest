# -*- coding: utf-8 -*-
"""
    Copyright (C) 2012 Kouhei Maeda <mkouhei@palmtb.net>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
from HTMLParser import HTMLParser
import xml.etree.ElementTree


# Movable Type format
class MtParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.text = ''
        self.temp = ''
        self.flag = ''
        self.fn_flag = ''
        self.nofn_flag = ''
        self.list_flag = ''
        self.img_src = ''
        self.img_alt = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'style':
            self.flag = 1
        if tag == 'div' and re.match('amazlet', str(attrs.get('class'))):
            self.flag = 1
        if tag == 'h4':
            self.flag = 'lv2'
        if tag == 'h5':
            self.flag = 'lv3'
        if tag == 'div' and str(attrs.get('class')) == 'footnote':
            self.fn_flag = 1
        if tag == 'p' and str(attrs.get('class')) == 'footnote':
            self.flag = 'fn'
        if tag == 'span' and str(attrs.get('class')) == 'footnote':
            self.flag = 'span-fn'
        if tag == 'ul':
            self.list_flag = 'ul'
        if tag == 'ol':
            self.list_flag = 'ol'
        if tag == 'li':
            self.flag = 'li'
        if tag == 'a':
            self.nofn_flag = 1
        if tag == 'img':
            self.img_src = str(attrs.get('src'))
            if attrs.get('alt'):
                self.img_alt = attrs.get('alt')

    def handle_data(self, data):
        if self.flag == 1:
            data = ''
        elif self.flag == 'lv2':
            self.text = (self.text + '\n' + data + '\n' +
                         '*' * (len(data.encode('utf-8')) - 2) * 2 + '\n\n')
        elif self.flag == 'lv3':
            self.text = (self.text + '\n' + data + '\n' +
                         '=' * (len(data.encode('utf-8')) - 2) * 2 + '\n\n')
        elif self.fn_flag:
            self.text = self.text + '\n\n'
        elif self.flag == 'fn':
            if self.nofn_flag:
                data = ''
            else:
                self.text = self.text + '.. [#] ' + data
        elif self.flag == 'span-fn':
            if self.nofn_flag:
                self.text = self.text + ' [#]_ '
        elif self.flag == 'li':
            self.text = self.text + '* ' + data
            #self.text = self.text + '#. ' + data + '\n'
        elif self.img_src:
            if self.img_alt:
                self.text = self.text + '\n.. image:: ' + self.img_src + \
                    '\n   :alt: ' + self.img_alt + '\n\n'
            else:
                self.text = self.text + '\n.. image:: ' + self.img_src + '\n\n'
        else:
            self.text += data

    def handle_endtag(self, tag):
        if (tag == 'h4' or tag == 'h5' or tag == 'p'
            or tag == 'span' or tag == 'li'):
            self.flag = ''
        if tag == 'a':
            self.nofn_flag = 0


# Hatena specify XML format
class HtnParser(object):

    def __init__(self, file):
        with open(file) as f:
            self.xmlobj = xml.etree.ElementTree.ElementTree(file=f)

    def list_days(self):
        return self.xmlobj.getroot().findall('day')

    def get_day_content(self, dayobj):
        date = dayobj.get('date')
        bodies = dayobj.find('body')
        comments = dayobj.find('comments')

        self.process_bodies(bodies)
        if comments is not None:
            self.process_comments(comments)

    # body starting is 1, not also 0
    def process_bodies(self, bodies):
        [self.process_body(body) for body in bodies.text.rsplit('\n*')]

    # processing body
    def process_body(self, body):
        if body:
            timestamp = self.get_timestamp(body)
            title = self.get_title(body)
            categories = self.get_categories(body)
            entry_body = self.get_entry_body(body)

            '''
            print(timestamp)
            print(title)
            print(categories)
            print(entry_body)
            '''

    # get timestamp of entry
    def get_timestamp(self, body):
        timestamp = body.split('*')[0]
        return timestamp

    # get title of entry
    def get_title(self, body):
        title = re.split('^\d*\*(\[.*\])*', body)[2].split('\n')[0]
        return title

    # get category of entry
    def get_categories(self, body):
        categories = []
        c = re.split('(\[(.*)\])', body)[2]
        if c.find(']['):
            [categories.append(category) for category in c.split('][')]
        else:
            categories.append(c)
        return categories

    # get body of entry
    def get_entry_body(self, body):
        if body.find('\n'):
            entry_body = body.split('\n', 1)[1]
            return entry_body

    # processing multiple comments
    def process_comments(self, comments):
        [self.process_comment(comment) for comment in comments]

    # print one comment
    def process_comment(self, comment):
        username = comment.find('username').text
        timestamp = comment.find('timestamp').text
        comment = comment.find('body').text

        '''
        formatting reST format of comment

        print(username)
        print(timestamp)
        print(comment)
        '''
