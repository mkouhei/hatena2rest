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
import os.path
import sys
import argparse
import processing
import utils
from __init__ import __version__


def parse_options():
    """Parse command line options"""
    prs = argparse.ArgumentParser(description='usage')
    prs.add_argument('-v', '--version', action='version', version=__version__)
    setoption(prs, 'retrieve')
    setoption(prs, 'infile')
    setoption(prs, 'dstdir')
    args = prs.parse_args()
    return args


def setoption(obj, kword):
    """Set option by keyword

    Argument:

        obj:   Parser object
        kword: Keyword of option
    """

    if kword == 'infile':
        obj.add_argument('infile', action='store',
                         help='specify input exported file of hatena diary')

    if kword == 'dstdir':
        obj.add_argument('-d', '--dstdir', action='store',
                         help='specify output destination directory path')

    if kword == 'retrieve':
        obj.add_argument('-r', '--retrieve', action='store_true',
                         help='retrieve image from web services')


def main():
    try:

        args = parse_options()
        f = args.__dict__.get('infile')
        if f.find('~') == 0:
            infile = os.path.expanduser(f)
        else:
            infile = os.path.abspath(f)

        if args.__dict__.get('dstdir'):
            dstdir = args.__dict__.get('dstdir')
        else:
            # default: ~/tmp/hatena2rest/
            dstdir = None

        if args.__dict__.get('retrieve'):
            retrieve_image_flag = True
        else:
            retrieve_image_flag = False

        processing.xml2rest(infile, dstdir, retrieve_image_flag)

    except RuntimeError as e:
        utils.error(e)
        return
    except UnboundLocalError as e:
        utils.error(e)
        return

if __name__ == '__main__':
    main()
