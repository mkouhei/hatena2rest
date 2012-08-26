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


class HatenaXMLParser(object):
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
        print('dirpath:' + date.replace('-', '/') + '/')

        # write entry to reST file.
        self.handle_body_elements(body_element)

        # write comments to reST file.
        if comments_element is not None:
            self.handle_comments_element(comments_element)

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
        [self.handle_body(body_text)
         for body_text in list_entries
         if body_text]

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

            print("title: %s" % title)
            print("timestamp: %s" % timestamp)
            print("categories: %s" % categories)
            print("body: %s" % rested_body)

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

        def parse_end_codeblock(string_line):
            """Parse end of codeblock.

            Argument:

                string_line: parsing target string.
            """
            pat_code_close, match_obj = self.regex_search(
                '^\|\|<|^\|<$', string_line)
            if match_obj:
                str_line = pat_code_close.sub('\n', string_line)
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
                    string_line = pat_code_open.sub(
                        '\n.. code-block:: ' +
                        match_obj.group(1) + '\n',
                        string_line)
                else:
                    string_line = pat_code_open.sub(
                        '\n.. code-block:: sh\n', string_line)
            return string_line

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

        if str_body:
            # str_line exclude '\n'
            for str_line in str_body.split('\n'):

                # convert hyperlink
                str_line = self.convert_hyperlink(str_line)

                # convert image from hatena fotolife
                str_line = self.fotolife2rest(str_line)

                # handle line inside code block
                if self.code_flag:
                    str_line = parse_end_codeblock(str_line)

                # handle line outside code block
                else:
                    str_line = parse_start_codeblock(str_line)

                    # listing
                    str_line = self.listing2rest(str_line)

                    # section , subsection
                    str_line = self.section2rest(str_line)

                    # convert footnote
                    str_line, footnotes_ = self.footnote2rest(str_line)
                    if footnotes_:
                        footnotes += footnotes_ + '\n'

                    # extract table data
                    table, tables = extract_tables(str_line, table, tables)

                    # remove hatena internal link
                    str_line = self.remove_hatena_internal_link(str_line)

                merge_string += str_line + '\n'

            # convert table
            merge_string = self.table2rest(tables, merge_string)

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
                merge_string = merge_string.replace(row[0], merge_row_str, 1)

        return merge_string

    def convert_hyperlink(self, str_line):
        """Convert hyperlink.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena [url:title:titlestring]
          to: reST `titlestring <url>`_
        """
        str_rested = str_line
        prog = re.compile(
            '(\[((http|https)://.+?):title=(.+?)\])', flags=re.U)
        for i in prog.findall(str_line):
            str_rested = str_rested.replace(
                i[0], ' `' + i[3] + ' <' + i[1] + '>`_ ')
        return str_rested

    def fotolife2rest(self, str_line):
        """Convert fotolife to image directive.

        Argument:

            string: text string of blog entry.

        convert is below
        from: hatena [f:id:imageid:image]
          to: reST .. image:: imgsrc
        """
        r, m = self.regex_search(
            '\[f:id:(.*):([0-9]*)[a-z]:image\]', str_line)
        if m:
            str_line = r.sub(
                ('\n.. image:: http://f.hatena.ne.jp/' +
                 m.group(1) + '/' + m.group(2) + '\n'), str_line)
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
        return str_line

    def section2rest(self, str_line):
        for i in range(2, 4)[::-1]:
            """2:section, 3:subsection"""
            sep = '-' if i == 2 else '^'
            r, m = self.regex_search('^(\*){%d}(.*)' % i, str_line)
            if m:
                str_line = r.sub(
                    '\n' + m.group(2) + '\n'
                    + sep * utils.length_str(m.group(2)) + '\n', str_line)

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
                footnotes += '.. [#] ' + i[1]
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

                title = self.convert_hyperlink(linked_title) + str_title

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

        pat_span_tag, m = self.regex_search(
            '(<span .+?>(.+?)</span>)', str_line)
        if m:
            str_line = pat_span_tag.sub(m.group(2), str_line)

        pat_del_tag, m = self.regex_search('(<del .+?>(.+?)</del>)', str_line)
        if m:
            str_line = pat_del_tag.sub('', str_line)

        # for google maps
        pat_google_maps, m = self.regex_search(
            '(<iframe .+?></iframe><br />(<.+?>.+?</.+?>)(.*?)</.+?>)',
            str_line)
        if m:
            str_line = pat_google_maps.sub(
                '\n.. raw:: html\n\n    ' + m.group(0) + '\n', str_line)

        # for image
        pat_amazon, m = self.regex_search('amazlet', str_line)
        if not m:
            pat_image, m = self.regex_search(
                '(<a href="(.+?)" .+?><img src="(.+?)".*?/?></.+?>)', str_line)
            if m:
                str_line = pat_image.sub(
                    '\n.. image:: ' + m.group(3) + '\n   :target: '
                    + m.group(2) + '\n\n', str_line)

        # for object
        pat_youtube, m = self.regex_search(
            '(<object .+?>(.*?)</.+?>)', str_line)
        if m:
            str_line = pat_youtube.sub(
                '\n.. raw:: html\n\n    ' + m.group(0) + '\n', str_line)

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
                    r = re.compile('<a.+?>')
                    tweet_msg = (r.sub('', m3.group(3)) +
                                 r.sub('', m3.group(4))
                                 + r.sub('', m3.group(5))).replace('</a>', '')

                uri = self.parse_blog_parts(str_tmp.encode('utf-8'))
                print tweet_msg
                print uri
                repl_str = '\n' + uri + ' ::\n\n   ' + tweet_msg + '\n\n'
                str_line = pat_comment.sub(repl_str, str_line)
                return str_line

        # for amazlet
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
            img_src = img_element.get('src')
            img_alt = img_element.get('alt')

            repl_amazon = ('\n.. figure:: ' + img_src + '\n   ' +
                           ':alt: ' + img_alt + '\n\n   `' + img_alt +
                           ' <' + uri + '>`_\n')
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

        xmltree = xml.etree.ElementTree.fromstring(string)

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
        print("comments:\n" + "-" * 10)
        [self.handle_comment_element(comment_element)
         for comment_element in comments_element]

    def handle_comment_element(self, comment_element):
        """Handles comment element.

        Argument:

            comment_element: comment element of XML.
        """

        username = comment_element.find('username').text
        print("username: %s" % username)

        unixtime = comment_element.find('timestamp').text
        timestamp = utils.unix2ctime(unixtime)
        print("timestamp: %s" % timestamp)

        comment = comment_element.find('body').text
        print("comment: %s" % self.comment2rest(comment))

    def comment2rest(self, comment_text):
        """Convert comment text to reST format.

        Argument:

            string: comment text.
        """

        # remove <br>
        pat_br_tag = re.compile('<br?>', flags=re.U)
        converted_comment = pat_br_tag.sub('', comment_text)
        return converted_comment
