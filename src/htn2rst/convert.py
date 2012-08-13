#!/usr/bin/env python
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

'''
Hatena diary export data format
---
0:AUTHOR, 1:TITLE, 3:DATE, 4:CATEGORY, 5:BODY, 6:COMMENT
 unused key: STATUS, ALLOW COMMENTS, CONVERT BREAKS, ALLOW PINGS,
 EXTENDED BODY, EXCERPT, KEYWORDS

 COMMENT: 6-1:AUTHOR, 6-2:EMAIL, 6-3:URL, 6-4:DATE, body(without key)
 unused key: IP
'''

import os
import shutil
import re
import sys
import htmllib
import pystache
from HTMLParser import HTMLParser


class Htn2Rest(pystache.View):
    template_path = '.'
    template_name = 'rest'
    template_encoding = 'utf-8'

    '''
    Read Hatena diary exported data with MT format
    '''
    def readFile(self):
        f = sys.argv[1]

        if os.path.isfile(f):
            self.f = open(f, 'r')

    def initialize(self):
        self.categories = self.comments = []
        self.YYYY = self.mm = self.dd = self.HH = self.MM = self.SS = ''
        self.c_YYYY = self.c_mm = self.c_dd = \
            self.c_HH = self.c_MM = self.c_SS = ''
        self.body = self.c_author = self.email = \
            self.siteurl = self.comment = ''
        self.body_flag = self.comment_flag = self.pre_flag = 0

    def datas(self):
        self.datas = self.dates = []
        dates = ''
        self.initialize()
        for line in self.f:
            if self.pre_flag == 0:
                self.getParam(line)
            self.getBody(line)
            self.getComment(line)
            self.closeEntry(line)

        master = 'out/master.rst.tmp'
        if not os.path.isfile(master):
            shutil.copyfile('master.tmpl', master)

        while len(self.dates) > 0:
            dates += self.dates.pop()

        f = open(master, 'a')
        f.write(dates)
        f.close()

    def generateEntry(self):
        self.entry = {}
        self.entry.update({
                "author": self.author,
                "title": self.title,
                "border": self.border,
                "year": self.YYYY,
                "month": self.mm,
                "date": self.dd,
                "hour": self.HH,
                "min": self.MM,
                "sec": self.SS,
                "categories": self.categories,
                "body": self.body
                })

    def generateComments(self):
        self.comments.append({
                "author": self.c_author,
                "email": self.email,
                "url": self.siteurl,
                "year": self.c_YYYY,
                "month": self.c_mm,
                "date": self.c_dd,
                "hour": self.c_HH,
                "min": self.c_MM,
                "sec": self.c_SS,
                "comment": self.comment
                })

    # Get blog data
    def getParam(self, line):

        # get author
        if self.re.match("^AUTHOR:", line):
            if self.comment_flag:
                self.c_author = unicode(line[:-1].split(':')[1], 'utf-8')
            else:
                self.author = unicode(line[:-1].split(': ')[1], 'utf-8')

        # get title
        elif self.re.match("^TITLE:", line):
            self.title = unicode(line[:-1].split(': ')[1], 'utf-8')
            self.border = "#" * len(self.title) * 2

        # get category
        elif self.re.match("^CATEGORY:", line):
            category = unicode(line[:-1].split(': ')[1], 'utf-8')
            self.categories.append({"category": category})

        # get timestamp
        elif self.re.match("^DATE:", line):
            self.getDate(line)

        # get email (comment)
        elif self.re.match("^EMAIL:", line):
            self.email = line[:-1].split(':')[1]

        # get URL (comment)
        elif self.re.match("^URL:", line):
            self.siteurl = line[:-1].split(': ')[1]

    # Get body
    def getBody(self, line):
        # outernal code-block
        if self.pre_flag == 0:
            if self.re.match("^BODY:", line):
                self.body_flag = 1
                self.body = ''
            elif self.body_flag == 1 and self.re.search('^-----$', line):
                self.body_flag = 0
            elif self.body_flag == 1 and self.re.match("^$", line):
                self.body = self.body
            elif (self.body_flag == 1 and
                  self.re.match('<pre>|<pre class(.)*', line)):
                self.pre_flag = 1
                self.body += '\n.. code-block:: none\n\n'
            elif self.body_flag == 1:
                self.body += self.parseHTML(re.sub('\t*', '', line))
        # internal code-block
        elif self.pre_flag == 1:
            if self.body_flag == 1 and self.re.match('</pre>', line):
                self.pre_flag = 0
                self.body += '\n\n'.encode('utf-8')
            else:
                if re.match('&#60;', line):
                    line = re.sub('&#60;', '<', line)
                elif re.match('&#62;', line):
                    line = re.sub('&#62;', '>', line)
                elif re.match('&#34;', line):
                    line = re.sub('&#34;', '"', line)
                elif re.match('&#38;', line):
                    line = re.sub('&#38;', '&', line)
                self.body += '   ' + self.parseHTML(line)

    # Get timestamp
    def getDate(self, line):
        date = line[:-1].split(': ')[1].split(' ')
        for i in range(3):
            if i == 0:
                if self.comment_flag:
                    self.c_mm = date[i].split('/')[0]
                    self.c_dd = date[i].split('/')[1]
                    self.c_YYYY = date[i].split('/')[2]
                else:
                    self.mm = date[i].split('/')[0]
                    self.dd = date[i].split('/')[1]
                    self.YYYY = date[i].split('/')[2]
            if i == 1:
                if self.comment_flag:
                    self.c_HH = date[i].split(':')[0]
                    self.c_MM = date[i].split(':')[1]
                    self.c_SS = date[i].split(':')[2]
                else:
                    self.HH = date[i].split(':')[0]
                    self.MM = date[i].split(':')[1]
                    self.SS = date[i].split(':')[2]
            if date[i] == "PM":
                if self.comment_flag:
                    self.c_HH = str(int(self.c_HH) + 12)
                else:
                    self.HH = str(int(self.HH) + 12)

    # Get comment
    def getComment(self, line):
        if self.re.match("^COMMENT:", line):
            self.comment_flag = 1
            self.comment = ''
        elif self.comment_flag == 1 and self.re.search('^-----$', line):
            self.generateComments()
        elif self.comment_flag == 1:
            self.getParam(line)
            if self.re.match("^(?!AUTHOR:|EMAIL:|IP:|URL:|DATE:)", line):
                self.comment += self.parseHTML(line[:-1])
        else:
            self.comments = []
            self.comment_flag = 0

    # Parse HTML format of body text
    def parseHTML(self, line):
        parser = ExtractData()
        parser.feed(unicode(line, 'utf-8'))
        parser.close()
        return parser.text

    # closing one blog entry
    def closeEntry(self, line):
        if re.search('^--------$', line) and self.pre_flag == 0:
            self.generateEntry()
            p = restView(self.entry, self.comments)
            p.context_list = p.data()
            dpath = (str(self.YYYY) + '/' + str(self.mm) +
                     '/' + str(self.dd) + '/')
            outpath = 'out/' + dpath
            if not os.path.isdir(outpath):
                os.makedirs(outpath)
            fbasename = str(self.HH) + str(self.MM) + str(self.SS)
            fname = fbasename + ".rst"
            fpath = outpath + fname
            self.dates.append('   ' + dpath + fbasename + '\n')
            f = open(fpath, 'w')
            f.write(p.render().encode('utf-8'))
            f.close()
            self.initialize()


class ExtractData(HTMLParser):

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


class restView(Htn2Rest):

    def __init__(self, entry, comments):
        self.entry = entry
        self.comments = comments

    def data(self):
        p = Htn2Rest()
        p.initialize()

        if self.comments:
            data = [{"entry":self.entry, "comments":self.comments}]
        else:
            data = [{"data":{"entry":self.entry}}]
        return data


def main():
    o = Htn2Rest()
    o.readFile()
    o.datas()
