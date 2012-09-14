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
import utils
import xml.etree.ElementTree


def replace_lexer(key):
    """Return code-block lexer.

    Argument:

        key: code block syntax name
    """

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


def convert_hyperlink(string):
    """Convert hyperlink.

    Argument:

        string: text string of blog entry.

    convert is
        from: hatena; [url:title:titlestring]
        to:   reST  ;  `titlestring <url>`_
    """

    pat_line_head = re.compile(
        '^(\[((http|https)://.+?):title=(.+?)\])', flags=re.U)
    for i in pat_line_head.findall(string):
        string = string.replace(
            i[0], '`' + i[3] + ' <' + i[1] + '>`_ ')

    pat_line_head2 = re.compile(
        '^( (`.+ <.+>`_))', flags=re.U)
    for i in pat_line_head2.findall(string):
        string = string.replace(i[0], i[1])

    pat_inline = re.compile(
            '(\[((http|https)://.+?):title=(.+?)\])', flags=re.U)
    for i in pat_inline.findall(string):
        string = string.replace(
            i[0], ' `' + i[3] + ' <' + i[1] + '>`_ ')

    return string


def replace_asterisk(string):
    """Replace asterisk

    Argument:

        string: text string of blog entry.
    """

    # except table header
    if string.find('|*') < 0:

        string = string.replace('*', '\*')

        if string.find('\*\*\*') == 0:
            string = string.replace('\*\*\*', '***', 1)
        elif string.find('\*\*') == 0:
            string = string.replace('\*\*', '**', 1)
        elif string.find('\*') == 0:
            string = string.replace('\*', '*', 1)

    return string


def replace_shell_variable(string):
    """Replace shell variable

    Argument:

        string: text string of blog entry.
    """

    pat_shell_var, match_obj = utils.regex_search(
        '(\${.+?}[a-zA-Z0-9/_\\\*]+)', string)
    if match_obj:
        string = pat_shell_var.sub(
            ' :command:`' + match_obj.group() + '` ', string)
    return string


def section2rest(string):
    """Convert hatena syntax to reST of section.

    Argument:

        string: text string of blog entry.
    """

    for i in range(2, 4)[::-1]:
        """2:section, 3:subsection"""
        sep = '-' if i == 2 else '^'
        r, m = utils.regex_search('^(\*){%d}(.*)' % i, string)
        if m:
            pat_space = re.compile('^\s+')
            section_str = pat_space.sub('', m.group(2))
            string = r.sub(
                '\n' + section_str + '\n'
                + sep * utils.length_str(section_str) + '\n', string)
    return string


def footnote2rest(string):
    """Convert hatena syntax to reST of footnote.

    Argument:

        string: text string of blog entry.

    convert is
        from: hatena; ((string))
        to:   reST  ; inline is   [#]_
                      footnote is .. [#] string
    """

    str_rest = string
    footnotes = ''
    pat_fn = re.compile('(\(\((.+?)\)\))', flags=re.U)

    for i in pat_fn.findall(string):
        str_rest = str_rest.replace(i[0], ' [#]_ ')
        if len(pat_fn.findall(string)) > 1:
            footnotes += '\n.. [#] ' + i[1]
        else:
            footnotes += '.. [#] ' + convert_hyperlink(i[1])
    return str_rest, footnotes


def extract_categories(str_categories):
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


def extract_entry_body(body_text):
    """Get body of entry.

    Argument:

        body_text: blog entry text.
    """

    if body_text.find('\n'):
        entry_body = body_text.split('\n', 1)[1]
        return entry_body


def handle_comments_element(comments_element):
    """Handle multiple comment within comments element.

    Argument:

        comments_element: comments element of XML.
    """

    comments = [handle_comment_element(comment_element)
                for comment_element in comments_element]
    return comments


def handle_comment_element(comment_element):
    """Handles comment element.

    Argument:

        comment_element: comment element of XML.
    """

    username = comment_element.find('username').text

    unixtime = comment_element.find('timestamp').text
    timestamp = utils.unix2ctime(unixtime)

    comment = comment_element.find('body').text

    return username, timestamp, comment


def parse_amazlet(xmltree):
    """Convert blog parts of amazlet to hyperlink

    Argument:

        xmltree: XML tree object

    """

    anchor_element = xmltree.find('div').find('a')
    img_element = anchor_element.find('img')

    uri = anchor_element.get('href')
    img_uri = img_element.get('src')
    img_alt = img_element.get('alt')
    repl_amazon = ('\n\n`' + img_alt + ' <' + uri + '>`_\n\n')
    return repl_amazon


def parse_twitter(xmltree):
    """Retrieve URI from blog parts of twitter

    Argument:

        xmltree: XML tree object

    """

    uri = [i.get('href') for i in xmltree.find('p')
           if i.get('title')][0]
    return uri


def parse_slideshare(xmltree):
    """Convert blog parts of slideshare to hyperlink

    Argument:

        xmltree: XML tree object

    """

    uri = xmltree.find('strong').find('a').get('href')
    title = xmltree.find('strong').find('a').get('title')
    repl_slideshare = '\n`' + title + ' <' + uri + '>`_\n'
    return repl_slideshare


def parse_heyquiz(xmltree):
    uri = xmltree.get('href')
    img_src = xmltree.find('img').get('src')
    img_alt = xmltree.find('img').get('alt')
    repl_heyquiz = '\n`' + img_alt + ' <' + img_src + '>`_\n'
    return repl_heyquiz


def convert_row(row, row_i, columns_width, row_str, border):
    """Convert row of table.

    Argument:

        row:           taple of row string of hatena syntax and columns values
        row_i:         row index
        columns_width: list of maximum width of each columns
        row_str:       converted row string
        border:        reST table border line string

    """

    for i in range(len(row[1])):
        # numbers of values
        if i < len(row[1]) - 1:
            row_str += ("  " + row[1][i] +
                        " " * (columns_width[i] -
                               utils.length_str(row[1][i])) + ' ')
            if row_i == 0:
                border += (" " + "=" * (columns_width[i] + 2))
        else:
            row_str += ("  " + row[1][i] +
                        " " * (columns_width[i]
                               - utils.length_str(row[1][i]))
                        + '  ')
            if row_i == 0:
                border += (" " + "=" * (columns_width[i] + 2) + ' ')
    return (row_str, border)


def get_columns_width_list(table, columns_width):
    """Retrieve list of maximum width of each columns.

    Argument:

        table:         list of rows
        columns_width: list of maximum width of each columns

    """

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


def merge_row_string(row_str, border):
    """Merge string from each rows

    Argument:

        row_str: row string merged each columns string
        border:  table border line string

    """

    merge_row_str = ''
    pat_row = re.compile(' \*')
    if pat_row.search(row_str):
        row_str = pat_row.sub('  ', row_str)
        merge_row_str += border + '\n' + row_str + '\n' + border
    else:
        merge_row_str += row_str
    return merge_row_str


def remove_span(string):
    """Remove span element.

    Argument:

        string: blog entry body string.

    """

    pat_span, m = utils.regex_search(
        '(<span .+?>(.+?)</span>)', string)
    if m:
        string = pat_span.sub(m.group(2), string)
    return string


def remove_del(string):
    """Remove del element.

    Argument:

        string: blog entry body string.

    """

    pat_del, m = utils.regex_search(
        '(<del( .+?|)>(.+?)</del>)', string)
    if m:
        string = pat_del.sub('', string)
    return string


def img2image(string):
    """Convert html img element to reST image directive.

    Argument:

        string: blog entry body string.

    """

    pat_img, m = utils.regex_search('^<img src="(.+?)" .+?(/?)>', string)
    if m:
        string = pat_img.sub('\n.. image:: ' + m.group(1)
                               + '\n\n', string)
    return string


def google_maps(string):
    """Convert blog parts of google maps to reST raw directive.

    Argument:

        string: blog entry body string.

    """

    if (string.find('http://maps.google.com/') > 0 or
        string.find('http://maps.google.co.jp/') > 0):
        pat_google_maps, m = utils.regex_search(
            '(<iframe .+?></iframe><br />(<.+?>.+?</.+?>)(.*?)</.+?>)',
            string)
        if m:
            string = pat_google_maps.sub(
                '\n.. raw:: html\n\n    ' + m.group(0) + '\n', string)
    return string


def gmodules(string):
    """Convert blog parts of gmodules to reST raw directive.

    Argument:

        string: blog entry body string.

    """

    if (string.find('http://gmodules.com') > 0 or
        string.find('https://gist.github.com') > 0):
        pat_gmodules, m = utils.regex_search(
            '^<script .+?></script>', string)
        if m:
            string = pat_gmodules.sub(
                '\n.. raw:: html\n\n    ' + m.group(0) + '\n', string)
    return string


def youtube(string):
    """Convert blog parts of YouTube to reST raw directive.

    Argument:

        string: blog entry body string.

    """

    if string.find('http://www.youtube.com') > 0:
        pat_youtube, m = utils.regex_search(
            '(<object .+?>(.*?)</.+?>)', string)
        if m:
            string = pat_youtube.sub(m.group(0), string)
            string = string.replace('\n', '')
            string = string.replace('&hl=ja', '')
            string = string.replace('&fs=1', '')
            string = '\n.. raw:: html\n\n   ' + string + '\n'
    return string


def get_metadata(string):
    """Get metadata of entry.

    Argument:

        string: title line string of hatena blog entry.
    """
    if string:
        """pattern a)

        timestamp: (\d*)
        category: (\[.*\])*
        title with uri converted: ( `.+ <.+>`_ )(.*)
        """
        pat_title_with_link = re.compile(
            '\*?(\d*)\*(\[.*\])*( `.+ <.+>`_ )(.*)',
            flags=re.U)

        """pattern b)

        timestamp: (\d*)
        category: (\[.*\])*
        title: (.*)
        """
        pat_title = re.compile(
            '\*?(\d*)\*(\[.*\])*(.*)', flags=re.U)

        if pat_title_with_link.search(string):
            # pattern a)
            timestamp, str_categories, linked_title, str_title = (
                pat_title_with_link.search(string).groups())

            title = convert_hyperlink(linked_title) + str_title

        elif pat_title.search(string):
            # pattern b)
            timestamp, str_categories, title = (
                pat_title.search(string).groups())

        return (utils.unix2ctime(timestamp, date_enabled=False),
                extract_categories(str_categories), title)


def parse_blog_parts(string):
    """Parse and convert blog parts.

    Argument:

        string: blog entry body string.

    """

    ex_ref_char = re.compile('\&(?!amp;)')
    string = ex_ref_char.sub('&amp;', string)

    string = string.replace('alt="no image"', '')

    try:
        xmltree = xml.etree.ElementTree.fromstring(string)
    except:
        utils.error(string)

    if xmltree.get('class') == 'amazlet-box':
        repl_amazon = parse_amazlet(xmltree)
        return repl_amazon
    if xmltree.get('class'):
        if xmltree.get('class').find('bbpBox') == 0:
            repl_twitter = parse_twitter(xmltree)
            return repl_twitter
    if str(xmltree.get('id')).find('__ss_') == 0:
        repl_slideshare = parse_slideshare(xmltree)
        return repl_slideshare
    if str(xmltree.get('href')).find('heyquiz.com') >= 0:
        repl_heyquiz = parse_heyquiz(xmltree)
        return repl_heyquiz


def extract_blog_parts(string):
    """Extract blog parts from blog entry string.

    Argument:

        string: blog entry body string.

    """

    html_tags = re.compile('(^(<.+?>(.+?)</.+?>)$)', flags=re.U)
    m = html_tags.search(string)
    if m:
        repl_str = parse_blog_parts(m.group(0).encode('utf-8'))
        string = html_tags.sub(repl_str, string)
    return string


def tweet(string):
    """Convert blog parts of twitter to reST hyperlink.

    Argument:

        string: blog entry body string.

    """

    pat_comment, m = utils.regex_search(
        '((<!-- (.+?) -->) (<.+?>(.+?)</.+?> )(<!-- (.+) -->))', string)
    if m:
        str_tmp = string.replace(m.group(2), '')
        str_tmp = str_tmp.replace(m.group(6), '')
        pat_style, m2 = utils.regex_search(
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

            if parse_blog_parts(str_tmp.encode('utf-8')):
                uri = parse_blog_parts(str_tmp.encode('utf-8'))
                repl_str = '\n' + uri + '::\n\n   ' + tweet_msg + '\n\n'
            else:
                repl_str = ''
            string = pat_comment.sub(repl_str, string)
    return string


def ditto(string):
    """Convert blog parts of twitter with ditto to reST hyperlink.

    Argument:

        string: blog entry body string.

    """

    pat_ditto, m = utils.regex_search(
        '(<style .+?>.+?</style>)(<div .+?>.+?</div>)', string)
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
        repl_str = '\n' + uri + '::\n\n   ' + tweet_msg + '\n\n'
        string = pat_ditto.sub(m.group(), repl_str).decode('utf-8')

    return string


def remove_internal_link(string):
    """Remove hatena internal link.

    Argument:

        string: blog entry body string.

    """

    pat_hatena_internal_link, m = utils.regex_search(
        '(\[\[|\]\])', string)
    if m:
        string = pat_hatena_internal_link.sub('', string)
    return string
