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
import time
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


class HtnParser(object):
    """ Hatena specify XML format"""

    def __init__(self, file):
        with open(file) as f:
            self.xmlobj = xml.etree.ElementTree.ElementTree(file=f)
            self.code_flag = False
            self.list_lv = 0

    def list_days(self):
        return self.xmlobj.getroot().findall('day')

    def get_day_content(self, dayobj):
        date = dayobj.get('date')
        bodies = dayobj.find('body')
        comments = dayobj.find('comments')
        print('dirpath:' + date.replace('-', '/') + '/')
        self.process_bodies(bodies)

        if comments is not None:
            self.process_comments(comments)

    """ body starting is 1, not also 0"""
    def process_bodies(self, bodies):

        """ remove comment out"""
        prog = re.compile('\n\<!--(.*\n)*--\>')

        """split multi entries per day,
        but except '*) in line head at code-block'
        """
        prog2 = re.compile('\n\*(?!\)|\*|\ |\n|/\d?\ \*)')

        bodies_ = re.sub(prog, '', bodies.text)
        entries = prog2.split(bodies_)

        [self.process_body(body) for body in entries if body]

    def process_body(self, body):
        """processing body"""

        if body:
            timestamp = self.get_timestamp(body)

            title = self.get_title(body)
            categories = self.get_categories(body)
            entry_body = self.get_entry_body(body)
            s = self.htn2rest(entry_body)

            print("title: %s" % title)
            print("timestamp: %s" % timestamp)
            print("categories: %s" % categories)
            print("body: %s" % s)

    def regex_search(self, pattern, string):
        r = re.compile(pattern, flags=re.U)
        m = r.search(string)
        return r, m

    def htn2rest(self, string):
        """Daily body text to rest format."""

        footnote = ''
        merge_string = ''
        if string:
            for s in string.split('\n'):

                """hyperlink conversion

                hatena [url:title:titlestring]
                reSt `titlestring <url>`_
                """
                r = re.compile(
                    '\[((http|https)://[a-zA-Z0-9\-_/\.%#&\?]*):title=(.*)\]',
                    flags=re.U)
                m = r.search(s)
                if m:
                    print(m.groups())
                    print("uri: %s" % m.group(1))
                    print("explanation: %s" % m.group(3))
                    s = r.sub(' `' + m.group(3) +
                              ' <' + m.group(1) + '>`_ ', s)

                # hatena fotolife
                r, m = self.regex_search(
                    '\[f:id:(.*):([0-9]*)[a-z]:image\]', s)
                if m:
                    s = r.sub(('\n.. image:: http://f.hatena.ne.jp/' +
                               m.group(1) + '/' + m.group(2) + '\n'), s)

                # inside code block
                if self.code_flag:
                    r, m = self.regex_search('^\|\|<|^\|<$', s)
                    if m:
                        s = r.sub('\n', s)
                        # code block closing
                        self.code_flag = False
                    else:
                        s = re.sub('^', '   ', s)

                # outside code block
                else:
                    r, m = self.regex_search('>\|([a-zA-Z0-9]*)\|$|>\|()$', s)
                    if m:
                        # code block opening
                        self.code_flag = True
                        if m.group(1):
                            s = r.sub('\n.. code-block:: '
                                       + m.group(1) + '\n', s)
                        else:
                            s = r.sub('\n.. code-block:: sh\n', s)

                    """list
                    3 is --- or +++
                    2 is -- or ++
                    1 is - or +
                    """
                    for i in range(1, 4)[::-1]:
                        r, m = self.regex_search(
                            '(^(-{%d}))|(^(\+{%d}))' % (i, i), s)
                        if m:
                            item = ('  ' * (i - 1) + '* ' if m.group(1)
                                    else '  ' * (i - 1) + '#. ')
                            if self.list_lv == i:
                                repl = item
                            else:
                                repl = '\n' + item
                                self.list_lv = i
                            s = r.sub(repl, s)

                    # 2:section, 3:subsection
                    for i in range(2, 4)[::-1]:
                        sep = '-' if i == 2 else '^'
                        r, m = self.regex_search('^(\*){%d}(.*)' % i, s)
                        if m:
                            s = r.sub(m.group(2) + '\n'
                                      + sep * len(m.group(2)) * i + '\n', s)

                    # footnote
                    r, m = self.regex_search('\(\((.*)\)\)', s)
                    if m:
                        s = r.sub(' [#]_ ', s)
                        footnote += '.. [#] ' + m.group(1) + '\n'

                    '''
                    r = re.compile(
                    '\[((http|https)://[a-zA-Z0-9\-_/\.%#&\?]*):title=(.*)\]',
                    flags=re.U)
                    m = r.search(footnote)
                    if m:
                        print(m.groups())
                        print("uri: %s" % m.group(1))
                        print("explanation: %s" % m.group(3))
                        footnote = r.sub(' `' + m.group(3) +
                                   ' <' + m.group(1) + '>`_ ', footnote)
                                   '''

                    # remove hatena syntax
                    r, m = self.regex_search('(\[\[|\]\])', s)
                    if m:
                        s = r.sub('', s)

                merge_string += s + '\n'
            return merge_string + '\n' + footnote

    def hyperlink(string):
        prog = re.compile(
            '\[(http?.://[\w\-_/\.~%#&\?]*):title=(?!<\[http?://.*)(.*)\]',
            flags=re.U)

    def get_metadata(self, string):
        if string:
            prog = re.compile('\*(\d*)\*(\[.*\])*(\[http?://.*\])(.*)')
            prog2 = re.compile('\*(\d*)\*(\[.*\])*(.*)')

            if prog.search(string):
                timestamp, categories, title_, title2_ =\
                    prog.search(string).groups()
            else:
                timestamp, categories, title = prog2.search(string).groups()

    def get_timestamp(self, string):
        """get timestamp of entry"""
        if string:
            prog = re.compile('\s+')
            timestamp = string.split('*')[0]
            date = prog.split(time.ctime(int(timestamp)))[3]
            return date

    def get_title(self, body):
        """get title of entry"""
        prog = re.compile('\n', flags=re.U)
        prog2 = re.compile('^\d*\*(\[.*\](\[http.*\]))*', flags=re.U)

        body_ = prog.split(body)[0]

        for i, v in enumerate(prog2.split(body_)):
            if i == 2:
                title = v
                return title

    def get_categories(self, body):
        """get category of entry"""
        categories = []
        prog = re.compile('^\d*\*(\[.*\])*(?!\[http.*\])', flags=re.U)
        prog2 = re.compile('^\[|\]$', flags=re.U)
        prog3 = re.compile('\]\[', flags=re.U)

        # remove [http://--/:title=hoge] from categories.

        text_ = prog.split(body, re.U)
        for i, v in enumerate(text_):
            if i == 1:
                # When exist category
                if v:
                    text2_ = prog2.sub('', v)
                    categories = prog3.split(text2_)
                    return categories

    def get_entry_body(self, body):
        """get body of entry"""
        if body.find('\n'):
            entry_body = body.split('\n', 1)[1]
            return entry_body

    def process_comments(self, comments):
        """processing multiple comments"""
        print("comments:\n" + "-" * 10)
        [self.process_comment(comment) for comment in comments]

    def process_comment(self, comment):
        """print one comment"""
        username = comment.find('username').text
        timestamp = comment.find('timestamp').text
        comment = comment.find('body').text

        '''
        formatting reST format of comment
        '''
        print("username: %s" % username)
        print("timestamp: %s" % timestamp)
        print("comment: %s" % self.comment2rest(comment))

    def comment2rest(self, string):
        # remove <br>
        r = re.compile('<br?>', flags=re.U)
        m = r.search(string)
        s = re.sub(r, '', string)
        return s
