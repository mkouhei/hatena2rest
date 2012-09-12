#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests of utils.py
"""
import unittest
import time
import hatena2rest.utils as u


class UtilsTests(unittest.TestCase):

    def setUp(self):
        self.unixtime = '2147483647'
        self.hankaku = u'abcABC123-%$s'
        self.zenkaku = u'日本語テスト'
        self.zenhankaku = u'日本語hogeほげ'
        self.html_str = '<del>100</del>もげ&nbsp;200&nbsp; 300\
 <span style="test">400</span>'
        self.html_str2 = '<span><del>100</del>もげ&nbsp;200&nbsp; 300\
 <span style="test">400</span></span>'
        self.regex = '<span(.+?|)>(.+?)</span>'

    def test_unix2ctime(self):
        if time.tzname == 'JST':
            self.assertEqual(u.unix2ctime(self.unixtime, date_enabled=False),
                             '121407')
            self.assertEqual(u.unix2ctime(self.unixtime),
                             'Tue Jan 19 12:14:07 2038')
        if time.timezone == 0:
            self.assertEqual(u.unix2ctime(self.unixtime, date_enabled=False),
                             '031407')
            self.assertEqual(u.unix2ctime(self.unixtime),
                             'Tue Jan 19 03:14:07 2038')

    def test_length_str(self):
        self.assertEqual(u.length_str(self.hankaku), 13)
        self.assertEqual(u.length_str(self.zenkaku), 12)
        self.assertEqual(u.length_str(self.zenhankaku), 14)

    def test_remove_element_entity(self):
        self.assertEqual(u.remove_element_entity(self.html_str),
                         'もげ&nbsp;200&nbsp; 300 400')
        self.assertEqual(u.remove_element_entity(self.html_str2),
                         '<span>もげ&nbsp;200&nbsp; 300 400')


if __name__ == '__main__':
    unittest.main()
