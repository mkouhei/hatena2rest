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

if __name__ == '__main__':
    unittest.main()
