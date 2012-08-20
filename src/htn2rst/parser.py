# -*- coding: utf-8 -*-
"""
Provides classes for parsing exported data of Hatena diary.

This module has two classes.
One is support for Movable Type format,
the other is support XML a.k.a. Hatena Diary format.

Developed for MovableType format, but it has many bugs of convering
hyperlink and footnote and more. Then rewriten for XML format against
squashing these bugs. So recommend using for XML format.

-------------------------------------------------------------------------------
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


class MtParser(HTMLParser):
    """
    For Movable Type format.
    But not developped now. not recomment to use this.
    """

    def __init__(self):
        """Initialize some parameters."""

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
        """Set flag when detecting HTML start tags."""

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
        """
        Convert html text to rest format data.

        Argument:

            data: a line of string for MT format text data.
        """

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
        """Clear flags when detecting HTML close tags."""
        if (tag == 'h4' or tag == 'h5' or tag == 'p'
            or tag == 'span' or tag == 'li'):
            self.flag = ''
        if tag == 'a':
            self.nofn_flag = 0


class HtnParser(object):
    """Hatena specify XML format."""

    def __init__(self, file):
        """Read exported XML file, and initialize parameters.

        Argument:

            file: exported file
        """
        with open(file) as f:
            self.xmlobj = xml.etree.ElementTree.ElementTree(file=f)
            self.code_flag = False
            self.table_flag = False
            self.list_lv = 0

    def list_days(self):
        return self.xmlobj.getroot().findall('day')

    def get_day_content(self, dayobj):
        """Get element of day, and process conversion

        Argument:

            dayobj: day element.
        """
        date = dayobj.get('date')
        bodies = dayobj.find('body')
        comments = dayobj.find('comments')
        print('dirpath:' + date.replace('-', '/') + '/')
        self.process_bodies(bodies)

        if comments is not None:
            self.handle_comments(comments)

    def process_bodies(self, bodies):
        """Separate data why body element has multi entry of diary.

        Starting is 1, not also 0.

        Argument:

            bodies: text string of body element from exported XML data.
        """

        # remove multiple lines comment.
        prog = re.compile('\n\<!--(.*\n)*--\>')
        bodies_ = re.sub(prog, '', bodies.text)

        """Separate text of multi entries of day excepting below cases;

        shell script switch default: \n\*(?!\))
        section, subsection: \n\*(?!\*)
        listing of reST: \n\*(?!\ )
        continuous line feed: \n(?!\n)
        crontab format: \n\*(?!/\d?\ \*)
        """
        prog2 = re.compile('\n\*(?!\)|\*|\ |\n|/\d?\ \*)')
        entries = prog2.split(bodies_)

        [self.handle_body(body) for body in entries if body]

    def handle_body(self, body):
        """Handle body.

        Argument:

            body: text string of one blog entry.
        """
        if body:
            timestamp, categories, title = self.get_metadata(
                body.split('\n', 1)[0])
            entry_body = self.get_entry_body(body)
            s = self.htn2rest(entry_body)

            print("title: %s" % title)
            print("timestamp: %s" % timestamp)
            print("categories: %s" % categories)
            print("body: %s" % s)

    def regex_search(self, pattern, string):
        """Prepare compilation of regex.

        Arguments:

            pattern: regex pattern
            string: processing target string

        return:

            r: compiled regex object
            m: searching result object
        """
        r = re.compile(pattern, flags=re.U)
        m = r.search(string)
        return r, m

    def htn2rest(self, string):
        """Convert body text of day entry to rest format.

        Argument:

            string: convert target string.
        """
        footnotes = ''
        table_data = []
        table = []
        tables = []
        merge_string = ''
        if string:
            for s in string.split('\n'):

                # hyperlink
                s = self.hyperlink(s)

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

                    for i in range(1, 4)[::-1]:
                        """list lv is indent depth
                        3 is --- or +++
                        2 is -- or ++
                        1 is - or +
                        """
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

                    for i in range(2, 4)[::-1]:
                        """2:section, 3:subsection"""
                        sep = '-' if i == 2 else '^'
                        r, m = self.regex_search('^(\*){%d}(.*)' % i, s)
                        if m:
                            s = r.sub(m.group(2) + '\n'
                                      + sep * len(m.group(2)) * i + '\n', s)

                    # footnote
                    s, footnotes_ = self.footnote(s)
                    if footnotes_:
                        footnotes += footnotes_ + '\n'

                    # table
                    r, m = self.regex_search('^\|(.+?)\|$', s)
                    if m:
                        raw_data = (m.group(0), m.groups()[0].split('|'))
                        if self.table_flag:
                            pass
                        else:
                            # table start
                            self.table_flag = True
                        table.append(raw_data)
                    else:
                        if self.table_flag:
                            # table close
                            tables.append(table)
                            table = []
                            self.table_flag = False

                    # remove hatena internal link
                    r, m = self.regex_search('(\[\[|\]\])', s)
                    if m:
                        s = r.sub('', s)

                merge_string += s + '\n'

            # replace table
            print(len(tables))
            #merge_string = merge_string.replace(table_i[0], table_i[1][0])

            return merge_string + '\n' + footnotes

    def table_column_width(self, tables):
        for raw_table in tables:
            print(raw_table)

    def hyperlink(self, string):
        """Convert hyperlink.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena [url:title:titlestring]
        to: reSt `titlestring <url>`_
        """
        string_ = string
        prog = re.compile(
            '(\[((http|https)://.+?):title=(.+?)\])', flags=re.U)
        for i in prog.findall(string):
            string_ = string_.replace(i[0], ' `' + i[3] + ' <' + i[1] + '>`_ ')
        return string_

    def footnote(self, string):
        """Convert footnote.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena: ((string))
        to: reST: inline is [#]_, footnote is .. [#] string
        """
        string_ = string
        footnotes = ''
        prog = re.compile('(\(\((.+?)\)\))', flags=re.U)

        for i in prog.findall(string):
            string_ = string_.replace(i[0], ' [#]_ ')
            if len(prog.findall(string)) > 1:
                footnotes += '\n.. [#] ' + i[1]
            else:
                footnotes += '.. [#] ' + i[1]
        return string_, footnotes

    def table(self, string):
        """Convert table.

        Argument:

            string: text string of blog entry.
        """
        prog = re.compile('^\|(.+?)\|$', flags=re.U)
        raw_data = prog.findall(string)[0].split('|')

    def get_metadata(self, string):
        """Get metadata of entry.

        Argument:

            string: title line string of hatena blog entry.
        """
        if string:
            '''pattern a)

            timestamp: (\d*)
            category: (\[.*\])*
            title with uri: (\[http?://.*\])(.*)
            '''
            prog = re.compile('\*?(\d*)\*(\[.*\])*(\[http?://.*\])(.*)',
                              flags=re.U)

            '''pattern b)

            timestamp: (\d*)
            category: (\[.*\])*
            title: (.*)
            '''
            prog2 = re.compile('\*?(\d*)\*(\[.*\])*(.*)', flags=re.U)

            if prog.search(string):
                # pattern a)
                timestamp, categories, linked_title, string_title =\
                    prog.search(string).groups()
                title = self.hyperlink(linked_title) + string_title
            elif prog2.search(string):
                # pattern b)
                timestamp, categories, title = prog2.search(string).groups()
            return (self.unix2ctime(timestamp),
                    self.get_categories(categories), title)

    def unix2ctime(self, unixtime):
        """Get timestamp of entry.

        Argument:

            unixtime: unixtime string
        """
        if unixtime:
            prog = re.compile('\s+')
            timestamp = prog.split(time.ctime(int(unixtime)))[3]
            return timestamp

    def get_categories(self, string):
        """Get category of entry.

        Argument:

           string: categories of hatena diary syntax format as [a][b][c]

        Return:

           list of categories.
        """
        if string:
            prog = re.compile('\[(.+?)\]', flags=re.U)
            categories = prog.findall(string)
            return categories

    def get_entry_body(self, body):
        """Get body of entry.

        Argument:

            body: blog entris text of body element.
        """
        if body.find('\n'):
            entry_body = body.split('\n', 1)[1]
            return entry_body

    def handle_comments(self, comments):
        """Handle multiple comment within comments element.

        Argument:

            comments: comments element.
        """
        print("comments:\n" + "-" * 10)
        [self.handle_comment(comment) for comment in comments]

    def handle_comment(self, comment):
        """Handles comment element.

        Argument:

            comment: comment element.
        """
        username = comment.find('username').text
        timestamp = comment.find('timestamp').text
        comment = comment.find('body').text

        print("username: %s" % username)
        print("timestamp: %s" % timestamp)
        print("comment: %s" % self.comment2rest(comment))

    def comment2rest(self, string):
        """Convert comment text to reST format.

        Argument:

            string: comment text.
        """
        # remove <br>
        r = re.compile('<br?>', flags=re.U)
        m = r.search(string)
        s = re.sub(r, '', string)
        return s
