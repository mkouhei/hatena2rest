# -*- coding: utf-8 -*-
"""
Provides utility function.

This module provides function as common utilities.

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
import sys
import re
import time
import unicodedata
if sys.version_info > (2, 6) and sys.version_info < (2, 8):
    import urllib2 as urllib
elif sys.version_info > (3, 0):
    import urllib.request as urllib
import socket
#socket.setdefaulttimeout(__timeout__)


def unix2ctime(unixtime, date_enabled=True):
    """Get timestamp of entry.

    Argument:

        unixtime: unixtime string
        date_enabled: 'Mon Apr  2 01:00:44 2012' when True
                      (default False '010044')
    """
    if unixtime:
        if date_enabled:
            # for comment
            timestamp = time.ctime(int(unixtime))
        else:
            # for blog entry.
            # reST file name becomes this value + '.rst'.
            prog = re.compile('\s+')
            t = prog.split(time.ctime(int(unixtime)))[3]
            timestamp = t.replace(':', '')
        return timestamp


def length_str(string):
    """calculate Hankaku(1 byte) and Zenkaku(2 byte) summarize length.

    Argument:

        string: calculate target string.

    Return:

        calculated length.
    """
    fwa = ['F', 'W', 'A']
    hnna = ['H', 'N', 'Na']

    zenkaku = len([unicodedata.east_asian_width(c)
                   for c in string
                   if unicodedata.east_asian_width(c) in fwa])
    hankaku = len([unicodedata.east_asian_width(c)
                   for c in string
                   if unicodedata.east_asian_width(c) in hnna])
    return (zenkaku * 2 + hankaku)


def retrieve_image(img_uri, img_src):
    obj = urllib.build_opener(urllib.HTTPHandler)
    for suffix in ('.jpg', '.png'):
        req = urllib.Request(img_uri + suffix)
        try:
            res = obj.open(req)
            data = res.read()
            with open(img_src, 'w') as f:
                f.write(data)
        except urllib.HTTPError as e:
            print(e)
        finally:
            return img_uri + suffix
