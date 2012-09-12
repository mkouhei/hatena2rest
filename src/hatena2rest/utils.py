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
import os
import glob
import time
import unicodedata
from datetime import datetime
if sys.version_info > (2, 6) and sys.version_info < (2, 8):
    import urllib2 as urllib
elif sys.version_info > (3, 0):
    import urllib.request as urllib
from __init__ import __sleep__
from __init__ import __timeout__
import socket


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

    if isinstance(string, unicode):
        zenkaku = len([unicodedata.east_asian_width(c)
                       for c in string
                       if unicodedata.east_asian_width(c) in fwa])
        hankaku = len([unicodedata.east_asian_width(c)
                       for c in string
                       if unicodedata.east_asian_width(c) in hnna])
        return (zenkaku * 2 + hankaku)
    elif isinstance(string, str):
        return len(string)


def remove_element_entity(string):

    # remove del element
    pat_del = re.compile('<del>.+?</del>')
    m = pat_del.search(string)
    if m:
        string = pat_del.sub('', string)

    # remove span_begin element
    pat_span_begin = re.compile('<span style=(.+?)>')
    m = pat_span_begin.search(string)
    if m:
        string = pat_span_begin.sub('', string)

    # remove span_end element
    string = string.replace('</span>', '')

    return string


def retrieve_image(img_uri, img_src_dir, retrieve_image_flag=False):

    def check_local_img(img_path):
        return os.path.isfile(img_path)

    def save_image(obj, req, img_path):

        res = obj.open(req)
        data = res.read()

        with open(img_path, 'w') as f:
            f.write(data)
            error('OK: ' + img_path)
            return True

    if not os.path.isdir(img_src_dir):
        os.makedirs(img_src_dir)

    # return image file path
    os.chdir(img_src_dir)
    if glob.glob(os.path.basename(img_uri + '*')):
        img_path = glob.glob(os.path.basename(img_uri + '*'))[0]
        if check_local_img(img_path):
            return img_path

    obj = urllib.build_opener(urllib.HTTPHandler)

    if img_uri.find('fotolife') > 0:

        # for hatena fotolife
        '''
        if check_local_img(img_path):
            return os.path.basename(img_path)
            '''

        for suffix in ('.jpg', '.png'):

            # return image file path
            get_img_path = (lambda img_src_dir, img_uri, suffix:
                                img_src_dir + os.path.basename(img_uri)
                            + suffix)
            img_path = get_img_path(img_src_dir, img_uri, suffix)

            if retrieve_image_flag:
                req = urllib.Request(img_uri + suffix)
                try:
                    socket.setdefaulttimeout(__timeout__)
                    save_image(obj, req, img_path)
                    time.sleep(__sleep__)

                except urllib.HTTPError as e:
                    error(e)
                    img_path = ''
                    continue

        return os.path.basename(img_path)
    else:
        # for exclude fotolife
        img_path = img_src_dir + os.path.basename(img_uri)

        '''
        if check_local_img(img_path):
            return os.path.basename(img_path)
            '''

        if retrieve_image_flag:
            req = urllib.Request(img_uri)
            try:
                if not check_local_img(img_path):
                    socket.setdefaulttimeout(__timeout__)
                    save_image(obj, req, img_path)
                    time.sleep(__sleep__)

            except urllib.HTTPError as e:
                error(e)
                img_path = ''

        return os.path.basename(img_path)


def regex_search(pattern, string):
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


def error(e):
    """Print standard error

    Argument:

        e: Error message
    """
    sys.stderr.write("ERROR: %s\n" % e)
