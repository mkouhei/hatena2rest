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
import os.path
import utils
import htnparser
import commands
from __init__ import __dstdir__


def xml2rest(infile, dstdir=None, retrieve_image_flag=False):

    if dstdir is None:
        dstdir = os.path.expanduser(__dstdir__)
    else:
        dstdir = os.patn.expanduser(dstdir)

    # make directory
    mkdir(dstdir)

    if not os.path.isfile(dstdir + 'conf.py'):
        # chdir to dstdir
        os.chdir(dstdir)

        # exec tinker setup
        commands.getstatusoutput('tinker -s')

    p = htnparser.HatenaXMLParser(infile, dstdir, retrieve_image_flag)

    path_str = '\n'
    for d in p.list_day_element():
        dirpath, bodies, comments = p.handle_entries_per_day(d)

        # make directory
        mkdir(dstdir + dirpath)

        for body in bodies[::-1]:

            timestamp = body[1]
            title = body[0]
            categories = body[2]
            body = body[3]

            # append path for master.rst
            path_str = '   ' + dirpath + timestamp + '\n' + path_str

            with open(dstdir + dirpath + timestamp + '.rst', 'w') as f:
                f.write(output(title, categories, body).encode('utf-8'))

            if comments:
                for comment in comments:
                    ''' '''

    with open(dstdir + 'master.rst', 'a') as f:
        f.write(path_str)


def mkdir(dirpath):
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)


def output(title, categories, body):
    body_str = (title + '\n' +
                '=' * utils.length_str(title) + '\n\n' +
                body + '\n\n' + footer(categories))
    return body_str


def footer(categories):
    pat_list = re.compile('\[|\]')
    footer_str = ('.. author:: default\n' +
            '.. categories:: ' + category(categories) + '\n' +
            '.. tags::\n' +
            '.. comments::\n')
    return footer_str


def category(categories=None):
    if categories is None:
        return ''
    cat_str = ''
    for cat in categories:
        cat_str += cat + ','
    return cat_str.rstrip(',')
