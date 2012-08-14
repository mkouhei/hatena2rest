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
import parser
import view


class Htn2Rest(object):
    '''
    Read Hatena diary exported data with MT format
    '''

    def __init__(self):
        self.categories = []
        self.comments = []
        self.YYYY = ''
        self.mm = ''
        self.dd = ''
        self.HH = ''
        self.MM = ''
        self.SS = ''
        self.c_YYYY = ''
        self.c_mm = ''
        self.c_dd = ''
        self.c_HH = ''
        self.c_MM = ''
        self.c_SS = ''
        self.body = ''
        self.c_author = ''
        self.email = ''
        self.siteurl = ''
        self.comment = ''
        self.body_flag = False
        self.comment_flag = False
        self.pre_flag = False

    def readFile(self):
        f = sys.argv[1]

        if os.path.isfile(f):
            self.f = open(f, 'r')

    def datas(self):
        self.datas = self.dates = []
        dates = ''
        self.initialize()
        for line in self.f:
            if not self.pre_flag:
                self.getParam(line)
            self.getBody(line)
            self.getComment(line)
            self.closeEntry(line)

        master = 'out/master.rst.tmp'
        if not os.path.isfile(master):
            shutil.copyfile('master.template', master)

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
        # internal code-block
        if self.pre_flag:
            if self.body_flag and re.match('</pre>', line):
                self.pre_flag = False
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
        # outernal code-block
        else:
            if re.match("^BODY:", line):
                self.body_flag = True
                self.body = ''
            elif self.body_flag:
                if re.search('^-----$', line):
                    self.body_flag = False
                elif re.match("^$", line):
                    #self.body = self.body
                    pass
                elif re.match('<pre>|<pre class(.)*', line):
                    self.pre_flag = True
                    self.body += '\n.. code-block:: none\n\n'
                else:
                    self.body += self.parseHTML(re.sub('\t*', '', line))

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
            self.comment_flag = True
            self.comment = ''
        elif self.comment_flag:
            if self.re.search('^-----$', line):
                self.generateComments()
            else:
                self.getParam(line)
                if self.re.match("^(?!AUTHOR:|EMAIL:|IP:|URL:|DATE:)", line):
                    self.comment += self.parseHTML(line[:-1])
        else:
            self.comments = []
            self.comment_flag = False

    # Parse HTML format of body text
    def parseHTML(self, line):
        parser = parser.HtnParse()
        parser.feed(unicode(line, 'utf-8'))
        parser.close()
        return parser.text

    # closing one blog entry
    def closeEntry(self, line):
        if re.search('^--------$', line) and not self.pre_flag:
            self.generateEntry()
            v = view.restView(self.entry, self.comments)
            v.context_list = v.data()
            dpath = ((str(self.YYYY) + '/' + str(self.mm) +
                      '/' + str(self.dd) + '/'))

            outpath = 'out/' + dpath
            if not os.path.isdir(outpath):
                os.makedirs(outpath)

            fbasename = str(self.HH) + str(self.MM) + str(self.SS)
            fname = fbasename + ".rst"

            fpath = outpath + fname

            self.dates.append('   ' + dpath + fbasename + '\n')

            with open(fpath, 'w') as f:
                f.write(v.render().encode('utf-8'))
                f.close()

            self.__init__()
