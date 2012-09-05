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
from HTMLParser import HTMLParser
import xml.etree.ElementTree
import utils
from __init__ import __imgdir__


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
                img_path = utils.retrieve_image(self.img_src,
                                                self.dstdir + __imgdir__,
                                                self.retrieve_image_flag)
                self.text = (self.text + '\n.. image:: ' + __imgdir__ +
                             img_path + '\n   :alt: ' + self.img_alt + '\n')
            else:
                self.text = (self.text + '\n.. image:: ' + __imgdir__ +
                             img_path + '\n')
        else:
            self.text += data

    def handle_endtag(self, tag):
        """Clear flags when detecting HTML close tags."""
        if (tag == 'h4' or tag == 'h5' or tag == 'p'
            or tag == 'span' or tag == 'li'):
            self.flag = ''
        if tag == 'a':
            self.nofn_flag = 0


class HatenaXMLParser(object):
    """Hatena specify XML format."""

    def __init__(self, file, dstdir, retrieve_image_flag=False):
        """Read exported XML file, and initialize parameters.

        Argument:

            file: exported file
        """
        with open(file) as f:
            self.xmlobj = xml.etree.ElementTree.ElementTree(file=f)
            self.code_flag = False
            self.table_flag = False
            self.list_lv = 0
            self.ref_flag = False
        self.retrieve_image_flag = retrieve_image_flag
        self.dstdir = dstdir

    def list_day_element(self):
        """Day element is daily unit of Hatena diary exported data,
        it has one blog entry or two or more entries.
        So handle per day element."""
        return self.xmlobj.getroot().findall('day')

    def handle_entries_per_day(self, day_element):
        """Get element of day, and process conversion

        Argument:

            day_element: day element of XML.
        """
        date = day_element.get('date')
        body_element = day_element.find('body')
        comments_element = day_element.find('comments')

        # make directory when it is not existed.
        dirpath = (date.replace('-', '/') + '/')

        # write entry to reST file.
        bodies = self.handle_body_elements(body_element)

        comments = None
        # write comments to reST file.
        if comments_element is not None:
            comments = self.handle_comments_element(comments_element)

        return dirpath, bodies, comments

    def handle_body_elements(self, body_element):
        """Separate data why body element has multi entry of diary.

        Starting is 1, not also 0.

        Argument:

            bodies: text string of body element from exported XML data.
        """

        # remove multiple lines of html comment.
        prog = re.compile('\n\<!--(.*\n)*--\>')
        bodies_text = re.sub(prog, '', body_element.text)

        """Separate text of multi entries with newline(\n),
        but excepting below cases;

        shell script switch default: \n\*(?!\))
        section, subsection: \n\*(?!\*)
        listing of reST: \n\*(?!\ )
        continuous line feed: \n(?!\n)
        crontab format: \n\*(?!/\d?\ \*)
        """
        prog2 = re.compile('\n\*(?!\)|\*|\ |\n|/\d?\ \*)')
        list_entries = prog2.split(bodies_text)

        # main loop
        # TODO: move to main() later.
        bodies = [self.handle_body(body_text)
                  for body_text in list_entries
                  if body_text]
        return bodies

    def handle_body(self, body_text):
        """Handle body.

        Argument:

            body_text: text string of one blog entry.
        """
        if body_text:
            timestamp, categories, title = self.get_metadata(
                body_text.split('\n', 1)[0])
            entry_body = self.extract_entry_body(body_text)
            rested_body = self.hatena2rest(entry_body)

            return title, timestamp, categories, rested_body

    def regex_search(self, pattern, string):
        """Prepare compilation of regex.

        Arguments:

            pattern: regex pattern
            string: processing target string

        return:

            pat_regex: compiled regex object
            match_obj: searching result object
        """
        pat_regex = re.compile(pattern, flags=re.U)
        match_obj = pat_regex.search(string)
        return pat_regex, match_obj

    def hatena2rest(self, str_body):
        """Convert body text of day entry to rest format.

        Argument:

            string: convert target string.
        """
        footnotes = ''
        table = []
        tables = []
        merge_string = ''

        def convert_start_ref(string_line):
            pat_start_ref, match_obj = self.regex_search(
                '^>((http|https)://(.+?)|)>$', string_line)
            if match_obj:
                self.ref_flag = True
                if match_obj.group(1):
                    repl_str = match_obj.group(1)
                else:
                    repl_str = ''

                string_line = pat_start_ref.sub(
                    repl_str,
                    string_line)

            return string_line

        def convert_end_ref(string_line):
            pat_end_ref, match_obj = self.regex_search(
                '^<<', string_line)
            if match_obj:
                string_line = pat_end_ref.sub('\n\n', string_line)
                self.ref_flag = False
            else:
                string_line = re.sub('^', '   ', string_line)
            return string_line

        def parse_end_codeblock(string_line):
            """Parse end of codeblock.

            Argument:

                string_line: parsing target string.
            """
            pat_code_close, match_obj = self.regex_search(
                '^\|\|<|^\|<$', string_line)
            if match_obj:
                string_line = pat_code_close.sub('\n', string_line)
                # code block closing
                self.code_flag = False
            else:
                string_line = re.sub('^', '   ', string_line)
            return string_line

        def parse_start_codeblock(string_line):
            pat_code_open, match_obj = self.regex_search(
                '>\|([a-zA-Z0-9]*)\|$|>\|()$', string_line)
            if match_obj:
                # code block opening
                self.code_flag = True
                if match_obj.group(1):
                    lexer_str = replace_lexer(match_obj.group(1))
                    string_line = pat_code_open.sub(
                        '\n.. code-block:: ' + lexer_str + '\n',
                        string_line)
                else:
                    string_line = pat_code_open.sub(
                        '\n.. code-block:: sh\n', string_line)
            return string_line

        def replace_lexer(key):
            lexer = {
                'conf': 'apache',
                'erlang': 'erlang',
                'm4': 'make',
                'log': 'ini',
                'lisp': 'scheme',
                'mail': 'ini',
                'rcs': 'diff',
                'dmesg': 'console',
                'strace': 'console',
                'fstab': 'ini',
                'tree': 'ini',
                'grub': 'ini',
                'emacs': 'scheme',
                'telnet': 'ini',
                'fetchmail': 'ini',
                'dot': 'ini',
                'git': 'diff',
                'TeX': 'latex',
                'Makefile': 'makefile',
                'sudoers': 'makefile',
                'crontab': 'sh',
                'dosbatch': 'bat',
                'sed': 'sh',
                'cc': 'c++',
                'mt': 'sh',
                'thml': 'ini',
                'xml': 'text'
                }
            if lexer.get(key):
                return lexer.get(key)
            else:
                return 'sh'

        def extract_tables(string_line, table, tables):
            pat_table, match_obj = self.regex_search(
                '^\|(.+?)\|$', string_line)
            if match_obj:
                row_data = (match_obj.group(0),
                            match_obj.groups()[0].split('|'))
                if not self.table_flag:
                    # table start
                    self.table_flag = True
                table.append(row_data)
            else:
                if self.table_flag:
                    # table close
                    tables.append(table)
                    table = []
                    self.table_flag = False
            return table, tables

        def replace_asterisk(string_line):
            # except table header
            if string_line.find('|*') < 0:
                string_line = string_line.replace('*', '\*')
                if string_line.find('\*\*\*') == 0:
                    string_line = string_line.replace('\*\*\*', '***', 1)
                elif string_line.find('\*\*') == 0:
                    string_line = string_line.replace('\*\*', '**', 1)
                elif string_line.find('\*') == 0:
                    string_line = string_line.replace('\*', '*', 1)
            return string_line

        def replace_shell_variable(string_line):
            pat_shell_var, match_obj = self.regex_search(
                '(\${.+?}[a-zA-Z0-9/_\\\*]+)', string_line)
            if match_obj:
                string_line = pat_shell_var.sub(
                    ' :command:`' + match_obj.group() + '` ', string_line)
            return string_line

        if str_body:
            # str_line exclude '\n'
            for str_line in str_body.split('\n'):

                # convert hyperlink
                str_line = self.convert_hyperlink(str_line)

                # handle line inside code block
                if self.code_flag:
                    str_line = parse_end_codeblock(str_line)

                # handle line outside code block
                else:
                    str_line = parse_start_codeblock(str_line)

                    # replace '*' to '\*' of inline
                    str_line = replace_asterisk(str_line)

                    # listing
                    str_line = self.listing2rest(str_line)

                    # convert shell var
                    str_line = replace_shell_variable(str_line)

                    # section , subsection
                    str_line = self.section2rest(str_line)

                    # convert image from hatena fotolife
                    str_line = self.fotolife2rest(str_line)

                    # convert footnote
                    str_line, footnotes_ = self.footnote2rest(str_line)
                    if footnotes_:
                        footnotes += footnotes_ + '\n'

                    # convert refs
                    if self.ref_flag:
                        str_line = convert_end_ref(str_line)
                    else:
                        str_line = convert_start_ref(str_line)

                    # extract table data
                    table, tables = extract_tables(str_line, table, tables)

                    # remove hatena internal link
                    str_line = self.remove_hatena_internal_link(str_line)

                merge_string += utils.remove_element_entity(str_line) + '\n'

            # convert table
            merge_string = self.table2rest(tables, merge_string)
            self.code_flag = False
            return merge_string + '\n' + footnotes

    def table2rest(self, tables, merge_string):

        def get_columns_width_list(table, columns_width):
            for row in table:
                '''
                row is tuple; (pattern, values)
                row[0] is pattern
                row[1] is values list
                '''
                for i in range(len(row[1])):
                    if columns_width[i] <= utils.length_str(row[1][i]):
                        columns_width[i] = utils.length_str(row[1][i])
                    else:
                        columns_width[i] = columns_width[i]
            return columns_width

        def convert_row(row, row_str, thead, tbody):

            for i in range(len(row[1])):
                # numbers of values
                if i < len(row[1]) - 1:
                    row_str += ("| " + row[1][i] +
                                " " * (columns_width[i] -
                                       utils.length_str(row[1][i])) + ' ')
                    if row_i == 0:
                        thead += ("+" + "=" * (columns_width[i] + 2))
                        tbody += ("+" + "-" * (columns_width[i] + 2))
                else:
                    row_str += ("| " + row[1][i] +
                                " " * (columns_width[i]
                                       - utils.length_str(row[1][i]))
                                + ' |\n')
                    if row_i == 0:
                        thead += ("+" + "=" * (columns_width[i] + 2) + '+')
                        tbody += ("+" + "-" * (columns_width[i] + 2) + '+')
            return (row_str, thead, tbody)

        def merge_row_string(row_str, thead, tbody):
            merge_row_str = ''
            prog = re.compile('\| \*')
            if prog.search(row_str):
                row_str = prog.sub('|  ', row_str)
                merge_row_str += thead + '\n' + row_str + thead
            else:
                merge_row_str += row_str + tbody
            return merge_row_str

        # replace table
        for table in tables:
            '''
            tables is list; [table, table, ...]
            table is list; [row, row]
            '''
            replace_line = ''
            thead = ''
            tbody = ''

            columns_width = [0] * len(table[1][1])

            # get columns width
            columns_width = get_columns_width_list(table, columns_width)

            # columns_width has max values when this step

            for row_i, row in enumerate(table):

                row_str = ''

                # get row string, row head border, row bottom border
                row_str, thead, tbody = convert_row(row, row_str, thead, tbody)

                # merge row string with row
                merge_row_str = merge_row_string(row_str, thead, tbody)

                # merge string with row string
                merge_string = merge_string.replace(
                    row[0] + '\n', merge_row_str, 1)

        return merge_string

    def convert_hyperlink(self, str_line):
        """Convert hyperlink.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena [url:title:titlestring]
          to: reST `titlestring <url>`_
        """

        pat_line_head = re.compile(
            '^(\[((http|https)://.+?):title=(.+?)\])', flags=re.U)
        for i in pat_line_head.findall(str_line):
            str_line = str_line.replace(
                i[0], '`' + i[3] + ' <' + i[1] + '>`_ ')

        pat_inline = re.compile(
            '(\[((http|https)://.+?):title=(.+?)\])', flags=re.U)
        for i in pat_inline.findall(str_line):
            str_line = str_line.replace(
                i[0], ' `' + i[3] + ' <' + i[1] + '>`_ ')

        return str_line

    def fotolife2rest(self, str_line):
        """Convert fotolife to image directive.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena [f:id:imageid:image]
          to: reST .. image:: imgsrc
                      :target: uri
        """
        r, m = self.regex_search(
            '\[f:id:(.*):([0-9]*)[a-z]:image(|:.+?)\]', str_line)
        if m:
            img_uri_partial = ('http://cdn-ak.f.st-hatena.com/images/fotolife/'
                               + m.group(1)[0] + '/' + m.group(1) + '/'
                               + m.group(2)[0:8] + '/' + m.group(2))
            # get image file
            img_src = utils.retrieve_image(img_uri_partial,
                                           self.dstdir + __imgdir__,
                                           self.retrieve_image_flag)
            utils.logging(img_src)
            repl_str = ('\n.. image:: ' + __imgdir__ + img_src)
            str_line = r.sub(repl_str, str_line)
        return str_line

    def listing2rest(self, str_line):
        for i in range(1, 4)[::-1]:
            """list lv is indent depth
            order is 3,2,1 why short matche is stronger than long.
            3 is --- or +++
            2 is -- or ++
            1 is - or +
            """
            r, m = self.regex_search(
                '(^(-{%d}))|(^(\+{%d}))' % (i, i), str_line)
            if m:
                item = ('  ' * (i - 1) + '* ' if m.group(1)
                        else '  ' * (i - 1) + '#. ')
                if self.list_lv == i:
                    repl = item
                else:
                    repl = '\n' + item
                    self.list_lv = i
                str_line = r.sub(repl, str_line)
        str_line += '\n'
        return str_line

    def section2rest(self, str_line):
        for i in range(2, 4)[::-1]:
            """2:section, 3:subsection"""
            sep = '-' if i == 2 else '^'
            r, m = self.regex_search('^(\*){%d}(.*)' % i, str_line)
            if m:
                pat_space = re.compile('^\s+')
                section_str = pat_space.sub('', m.group(2))
                str_line = r.sub(
                    '\n' + section_str + '\n'
                    + sep * utils.length_str(section_str) + '\n', str_line)
        return str_line

    def footnote2rest(self, str_line):
        """Convert footnote.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena: ((string))
          to: reST:   inline is [#]_
                    footnote is .. [#] string
        """
        str_rest = str_line
        footnotes = ''
        prog = re.compile('(\(\((.+?)\)\))', flags=re.U)

        for i in prog.findall(str_line):
            str_rest = str_rest.replace(i[0], ' [#]_ ')
            if len(prog.findall(str_line)) > 1:
                footnotes += '\n.. [#] ' + i[1]
            else:
                footnotes += '.. [#] ' + self.convert_hyperlink(i[1])
        return str_rest, footnotes

    def table(self, string):
        """Convert table.

        Argument:

            string: text string of blog entry.
        """
        prog = re.compile('^\|(.+?)\|$', flags=re.U)
        row_data = prog.findall(string)[0].split('|')

    def get_metadata(self, str_title_line):
        """Get metadata of entry.

        Argument:

            string: title line string of hatena blog entry.
        """
        if str_title_line:
            '''pattern a)

            timestamp: (\d*)
            category: (\[.*\])*
            title with uri: (\[http?://.*\])(.*)
            '''
            pat_title = re.compile('\*?(\d*)\*(\[.*\])*(\[http?://.*\])(.*)',
                              flags=re.U)

            '''pattern b)

            timestamp: (\d*)
            category: (\[.*\])*
            title: (.*)
            '''
            pat_title_with_link = re.compile(
                '\*?(\d*)\*(\[.*\])*(.*)', flags=re.U)

            if pat_title.search(str_title_line):
                # pattern a)
                timestamp, str_categories, linked_title, str_title = (
                    pat_title.search(str_title_line).groups())

                title = self.convert_hyperlink(
                    linked_title) + str_title

            elif pat_title_with_link.search(str_title_line):
                # pattern b)
                timestamp, str_categories, title = (
                    pat_title_with_link.search(str_title_line).groups())

            return (utils.unix2ctime(timestamp, date_enabled=False),
                    self.extract_categories(str_categories), title)

    def remove_hatena_internal_link(self, str_line):
        pat_hatena_internal_link, m = self.regex_search(
            '(\[\[|\]\])', str_line)
        if m:
            str_line = pat_hatena_internal_link.sub('', str_line)

        # for ditto
        pat_ditto, m = self.regex_search(
            '(<style .+?>.+?</style>)(<div .+?>.+?</div>)',
            str_line)
        if m:
            ex_ref_char = re.compile('\&(?!amp;)', flags=re.U)
            string = ex_ref_char.sub('&amp;', m.group(2))

            # get uri
            uri = ''
            xmltree = xml.etree.ElementTree.fromstring(string.encode('utf-8'))
            for p_child in xmltree.find('p').getchildren():
                for i, p_child_child in enumerate(p_child.getchildren()):
                    if i == 1 and p_child_child.get('href'):
                        uri = p_child_child.get('href')
            #utils.logging(uri, debug)

            # get tweet message
            tweet_msg = ''
            if xmltree.get('class').find('ditto') == 0:
                span_element = xmltree.find('p').find('span').find('span')
                for i, v in enumerate(xmltree.itertext()):
                    if i > 1:
                        pat = re.compile('&nbsp;|via', flags=re.U)
                        if pat.search(v) > 0:
                            break
                        else:
                            tweet_msg += str(v.encode('utf-8'))
            #utils.logging(tweet_msg, debug)
            repl_str = '\n' + uri + '::\n\n   ' + tweet_msg + '\n\n'
            str_line = pat_ditto.sub(m.group(), repl_str).decode('utf-8')

        pat_span_tag, m = self.regex_search(
            '(<span .+?>(.+?)</span>)', str_line)
        if m:
            str_line = pat_span_tag.sub(m.group(2), str_line)

        pat_del_tag, m = self.regex_search(
            '(<del( .+?|)>(.+?)</del>)', str_line)
        if m:
            str_line = pat_del_tag.sub('', str_line)

        # for google maps
        if (str_line.find('http://maps.google.com/') > 0 or
            str_line.find('http://maps.google.co.jp/') > 0):
            pat_google_maps, m = self.regex_search(
                '(<iframe .+?></iframe><br />(<.+?>.+?</.+?>)(.*?)</.+?>)',
                str_line)
            if m:
                str_line = pat_google_maps.sub(
                    '\n.. raw:: html\n\n    ' + m.group(0) + '\n', str_line)

        # for gmodules
        if (str_line.find('http://gmodules.com') > 0 or
            str_line.find('https://gist.github.com') > 0):
            pat_gmodules, m = self.regex_search(
                '^<script .+?></script>', str_line)
            if m:
                str_line = pat_gmodules.sub(
                    '\n.. raw:: html\n\n    ' + m.group(0) + '\n', str_line)

        # for img element
        pat_img, m = self.regex_search('^<img src="(.+?)" .+?(/?)>', str_line)
        if m:
            str_line = pat_img.sub('\n.. image:: ' + m.group(1)
                                   + '\n\n', str_line)

        # for image
        pat_amazon, m = self.regex_search('amazlet', str_line)
        if not m:
            pat_image, m = self.regex_search(
                '(<a href="(.+?)" .+?><img src="(.+?)".*?/?></.+?>)', str_line)
            if m:
                img_path = utils.retrieve_image(m.group(3),
                                                self.dstdir + __imgdir__,
                                                self.retrieve_image_flag)
                str_line = pat_image.sub(
                    '\n.. image:: ' + __imgdir__ + img_path + '\n   :target: '
                    + m.group(2) + '\n\n', str_line)

        # for object
        if str_line.find('http://www.youtube.com') > 0:
            pat_youtube, m = self.regex_search(
                '(<object .+?>(.*?)</.+?>)', str_line)
            if m:
                str_line = pat_youtube.sub(m.group(0), str_line)
                str_line = str_line.replace('\n', '')
                str_line = str_line.replace('&hl=ja', '')
                str_line = str_line.replace('&fs=1', '')
                str_line = '\n.. raw:: html\n\n   ' + str_line + '\n'

        # for tweet
        pat_comment, m = self.regex_search(
            '((<!-- (.+?) -->) (<.+?>(.+?)</.+?> )(<!-- (.+) -->))', str_line)
        if m:
            str_tmp = str_line.replace(m.group(2), '')
            str_tmp = str_tmp.replace(m.group(6), '')
            pattern_style, m2 = self.regex_search(
                ' <style .+?>(.+?)</style> ', str_tmp)
            if m2:
                str_tmp = str_tmp.replace(m2.group(0), '')
                str_tmp = str_tmp.replace('><', '>\n<')
                str_tmp = str_tmp.replace('> <', '>\n<')
                str_tmp = str_tmp.replace('</span>\n', '')
                pat_tweet = re.compile(
                    '((<.+?>(.+?)</.+?>)(.+?)(<.+?>(.+?)</.+?>))')
                m3 = pat_tweet.search(str_tmp)
                if m3:
                    pat_anchor = re.compile('<a.+?>')
                    tweet_msg = (pat_anchor.sub('', m3.group(3)) +
                                 pat_anchor.sub('', m3.group(4))
                                 + pat_anchor.sub('', m3.group(5))
                                 ).replace('</a>', '')

                if self.parse_blog_parts(str_tmp.encode('utf-8')):
                    uri = self.parse_blog_parts(str_tmp.encode('utf-8'))
                    repl_str = '\n' + uri + '::\n\n   ' + tweet_msg + '\n\n'
                else:
                    repl_str = ''
                str_line = pat_comment.sub(repl_str, str_line)
                return str_line

        # for blogparts
        html_tags = re.compile('(^(<.+?>(.+?)</.+?>)$)', flags=re.U)
        m = html_tags.search(str_line)
        if m:
            repl_str = self.parse_blog_parts(m.group(0).encode('utf-8'))
            str_line = html_tags.sub(repl_str, str_line)
        return str_line

    def parse_blog_parts(self, string):

        ex_ref_char = re.compile('\&(?!amp;)')
        string = ex_ref_char.sub('&amp;', string)

        string = string.replace('alt="no image"', '')

        def parse_amazlet(xmltree):
            anchor_element = xmltree.find('div').find('a')
            img_element = anchor_element.find('img')

            uri = anchor_element.get('href')
            img_uri = img_element.get('src')
            img_alt = img_element.get('alt')
            repl_amazon = ('\n\n`' + img_alt + ' <' + uri + '>`_\n\n')
            return repl_amazon

        def parse_twitter(xmltree):
            uri = [i.get('href') for i in xmltree.find('p')
                   if i.get('title')][0]
            return uri

        def parse_slideshare(xmltree):
            uri = xmltree.find('strong').find('a').get('href')
            title = xmltree.find('strong').find('a').get('title')
            repl_slideshare = '\n`' + title + ' <' + uri + '>`_\n'
            return repl_slideshare

        try:
            xmltree = xml.etree.ElementTree.fromstring(string)
        except:
            print string

        if xmltree.get('class') == 'amazlet-box':
            repl_amazon = parse_amazlet(xmltree)
            return repl_amazon
        if xmltree.get('class'):
            if xmltree.get('class').find('bbpBox') == 0:
                repl_twitter = parse_twitter(xmltree)
                return repl_twitter
        if xmltree.get('id').find('__ss_') == 0:
            repl_slideshare = parse_slideshare(xmltree)
            return repl_slideshare

    def extract_categories(self, str_categories):
        """Get category of entry.

        Argument:

            str_categories: categories of hatena diary syntax as [a][b][c]

        Return:

           list of categories.
        """
        if str_categories:
            pat_category = re.compile('\[(.+?)\]', flags=re.U)
            list_category = pat_category.findall(str_categories)
            return list_category

    def extract_entry_body(self, body_text):
        """Get body of entry.

        Argument:

            body_text: blog entry text.
        """
        if body_text.find('\n'):
            entry_body = body_text.split('\n', 1)[1]
            return entry_body

    def handle_comments_element(self, comments_element):
        """Handle multiple comment within comments element.

        Argument:

            comments_element: comments element of XML.
        """
        comments = [self.handle_comment_element(comment_element)
                         for comment_element in comments_element]
        return comments

    def handle_comment_element(self, comment_element):
        """Handles comment element.

        Argument:

            comment_element: comment element of XML.
        """
        username = comment_element.find('username').text

        unixtime = comment_element.find('timestamp').text
        timestamp = utils.unix2ctime(unixtime)

        comment = comment_element.find('body').text

        return username, timestamp, comment

    def comment2rest(self, comment_text):
        """Convert comment text to reST format.

        Argument:

            string: comment text.
        """

        # remove <br>
        pat_br_tag = re.compile('<br?>', flags=re.U)
        converted_comment = pat_br_tag.sub('', comment_text)
        return converted_comment
