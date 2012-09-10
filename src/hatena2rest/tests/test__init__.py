#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests of __init__.py
"""
import unittest
import hatena2rest


class InitTests(unittest.TestCase):
    def test_version_defined(self):
        actual_version = hatena2rest.__version__
        self.assertTrue(actual_version)

    def test_sleep_defined(self):
        actual_sleep = hatena2rest.__sleep__
        self.assertTrue(actual_sleep)

    def test_timeout_defined(self):
        actual_timeout = hatena2rest.__timeout__
        self.assertTrue(actual_timeout)

    def test_log_defined(self):
        actual_log = hatena2rest.__log__
        self.assertTrue(actual_log)

    def test_dstdir_defined(self):
        actual_dstdir = hatena2rest.__dstdir__
        self.assertTrue(actual_dstdir)

    def test_imgdir_defined(self):
        actual_imgdir = hatena2rest.__imgdir__
        self.assertTrue(actual_imgdir)

if __name__ == '__main__':
    unittest.main()
