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
from __init__ import __version__


def parse_options():
    prs = argparse.ArgumentParser(description='usage')
    prs.add_argument('-V', '--version', action='version', version=__version__)
    setoption(prs, 'infile')
    setoption(prs, 'dstpath')
    args = prs.parse_args()
    return args


def setoption(obj, kword):
    if kword == 'infile':
        obj.add_argument('infile', action='store',
                         help='specify input exported file of hatena diary')

    if kword == 'dstpath':
        obj.add_argument('-d', '--dstpath', action='store',
                         help='specify output destination directory path')


def error(e):
    sys.stderr.write("ERROR: %s\n" % e)


def main():
    try:
        args = parse_options()
        args.func(args)

        o = Htn2Rest()
        o.readFile()
        o.datas()

    except RuntimeError as e:
        error(e)
        return
    except UnboundLocalError as e:
        error(e)
        return


if __name__ == '__main__':
    main()
