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
import convert
from __init__ import __imgdir__


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
            comments = convert.handle_comments_element(comments_element)

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
            body_text = convert.convert_hyperlink(body_text)
            timestamp, categories, title = convert.get_metadata(
                body_text.split('\n', 1)[0])
            entry_body = convert.extract_entry_body(body_text)
            rested_body = self.hatena2rest(entry_body)

            return title, timestamp, categories, rested_body

    def hatena2rest(self, str_body):
        """Convert body text of day entry to rest format.

        Argument:

            string: convert target string.
        """
        footnotes = ''
        table = []
        tables = []
        merge_string = ''

        def parse_begin_ref(string_line):
            """Parse begining of reference block

            Argument:

                string: convert target string.
            """
            pat_start_ref, match_obj = utils.regex_search(
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

        def parse_end_ref(string_line):
            """Parse ending of reference block

            Argument:

                string: convert target string.
            """
            pat_end_ref, match_obj = utils.regex_search(
                '^<<', string_line)
            if match_obj:
                string_line = pat_end_ref.sub('\n\n', string_line)
                self.ref_flag = False
            else:
                string_line = re.sub('^', '   ', string_line)
            return string_line

        def parse_begin_codeblock(string_line):
            """Parse begining of code block

            Argument:

                string: convert target string.
            """
            pat_code_open, match_obj = utils.regex_search(
                '>\|([a-zA-Z0-9]*)\|$|>\|()$', string_line)
            if match_obj:
                # code block opening
                self.code_flag = True
                if match_obj.group(1):
                    lexer_str = convert.replace_lexer(match_obj.group(1))
                    string_line = pat_code_open.sub(
                        '\n.. code-block:: ' + lexer_str + '\n',
                        string_line)
                else:
                    string_line = pat_code_open.sub(
                        '\n.. code-block:: sh\n', string_line)
            return string_line

        def parse_end_codeblock(string_line):
            """Parse ending of codeblock.

            Argument:

                string_line: parsing target string.
            """
            pat_code_close, match_obj = utils.regex_search(
                '^\|\|<|^\|<$', string_line)
            if match_obj:
                string_line = pat_code_close.sub('\n', string_line)
                # code block closing
                self.code_flag = False
            else:
                string_line = re.sub('^', '   ', string_line)
            return string_line

        def extract_tables(string_line, table, tables):
            """Extract tables

            Argument:

                string_line: parsing target string.
                table:       parsing target table
                tables:      parsing target tables
            """
            pat_table, match_obj = utils.regex_search(
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
                str_line = convert.convert_hyperlink(str_line)

                # handle line inside code block
                if self.code_flag:
                    str_line = parse_end_codeblock(str_line)

                # handle line outside code block
                else:
                    str_line = parse_begin_codeblock(str_line)

                    # replace '*' to '\*' of inline
                    str_line = convert.replace_asterisk(str_line)

                    # listing
                    str_line = self.listing2rest(str_line)

                    # convert shell var
                    str_line = convert.replace_shell_variable(str_line)

                    # section , subsection
                    str_line = convert.section2rest(str_line)

                    # convert image from hatena fotolife
                    str_line = self.fotolife2rest(str_line)

                    # convert footnote
                    str_line, footnotes_ = convert.footnote2rest(str_line)
                    if footnotes_:
                        footnotes += footnotes_ + '\n'

                    # convert refs
                    if self.ref_flag:
                        str_line = parse_end_ref(str_line)
                    else:
                        str_line = parse_begin_ref(str_line)

                    # extract table data
                    table, tables = extract_tables(str_line, table, tables)

                    # remove internal_link and convert blog parts
                    str_line = self.convert_blog_parts(str_line)

                merge_string += utils.remove_element_entity(str_line) + '\n'

            # convert table
            merge_string = self.table2rest(tables, merge_string)
            self.code_flag = False
            return merge_string + '\n' + footnotes

    def table2rest(self, tables, merge_string):
        """Convert hatena syntax to reST of table

            Argument:

                tables:       list of table
                merge_string: convertd and concatnated strings
        """

        # replace table
        for table in tables:
            """
            tables is list: [table, table, ...]
            table is list:  [row, row]
            """
            replace_line = ''
            border = ''

            columns_width = [0] * len(table[1][1])

            # get columns width
            columns_width = convert.get_columns_width_list(
                table, columns_width)

            # columns_width has max values when this step
            for row_i, row in enumerate(table):

                row_str = ''
                # get row string, row border
                row_str, border = convert.convert_row(
                    row, row_i, columns_width, row_str, border)

                # merge row string with row
                merge_row_str = convert.merge_row_string(row_str, border)

                # merge string with row string
                if row_i == len(table) - 1:
                    merge_string = merge_string.replace(
                        row[0] + '\n', merge_row_str + '\n' + border, 1)
                else:
                    merge_string = merge_string.replace(
                        row[0] + '\n', merge_row_str, 1)

        return merge_string

    def fotolife2rest(self, str_line):
        """Convert fotolife to image directive.

        Argument:

            str_line: text string of blog entry.

        convert is
            from: hatena; [f:id:imageid:image]
            to:   reST  ; .. image:: imgsrc
                              :target: uri
        """
        r, m = utils.regex_search(
            '\[f:id:(.*):([0-9]*)[a-z]:image(|:.+?)\]', str_line)
        if m:
            img_uri_partial = ('http://cdn-ak.f.st-hatena.com/images/fotolife/'
                               + m.group(1)[0] + '/' + m.group(1) + '/'
                               + m.group(2)[0:8] + '/' + m.group(2))
            # get image file
            img_src = utils.retrieve_image(img_uri_partial,
                                           self.dstdir + __imgdir__,
                                           self.retrieve_image_flag)
            repl_str = ('\n.. image:: ' + __imgdir__ + img_src)
            str_line = r.sub(repl_str, str_line)
        return str_line

    def listing2rest(self, str_line):
        """Convert hatena syntax to reST of list.

        Argument:

            str_line: text string of blog entry.

        """

        for i in range(1, 4)[::-1]:
            """list lv is indent depth
            order is 3,2,1 why short matche is stronger than long.
            3 is --- or +++
            2 is -- or ++
            1 is - or +
            """
            r, m = utils.regex_search(
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

    def convert_blog_parts(self, str_line):
        """Convert blog parts to reST.

        Argument:

            str_line: text string of blog entry.

        """

        # remove hatena internal link
        str_line = convert.remove_internal_link(str_line)

        # for ditto
        str_line = convert.ditto(str_line)

        # remove span element
        str_line = convert.remove_span(str_line)

        # remove del element
        str_line = convert.remove_del(str_line)

        # for google maps
        str_line = convert.google_maps(str_line)

        # for gmodules
        str_line = convert.gmodules(str_line)

        # for img element
        str_line = convert.img2image(str_line)

        # for amazlet
        pat_amazon, m = utils.regex_search('amazlet', str_line)
        if not m:
            pat_image, m = utils.regex_search(
                '(<a href="(.+?)" .+?><img src="(.+?)".*?/?></.+?>)', str_line)
            if m:
                img_path = utils.retrieve_image(m.group(3),
                                                self.dstdir + __imgdir__,
                                                self.retrieve_image_flag)
                str_line = pat_image.sub(
                    '\n.. image:: ' + __imgdir__ + img_path + '\n   :target: '
                    + m.group(2) + '\n\n', str_line)

        # for youtube
        str_line = convert.youtube(str_line)

        # for tweet
        str_line = convert.tweet(str_line)

        # for blogparts
        str_line = convert.extract_blog_parts(str_line)

        return str_line

    def comment2rest(self, comment_text):
        """Convert comment text to reST format.

        Argument:

            comment_text: comment text.
        """

        # remove <br>
        pat_br_tag = re.compile('<br?>', flags=re.U)
        converted_comment = pat_br_tag.sub('', comment_text)
        return converted_comment
