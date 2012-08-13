#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests of __init__.py
"""
import unittest
import htn2rst


class InitTests(unittest.TestCase):
    def test_version_defined(self):
        actual_version = htn2rst.__version__
        self.assertTrue(actual_version)

if __name__ == '__main__':
    unittest.main()
