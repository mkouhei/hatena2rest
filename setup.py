#!/usr/bin/env python
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

import os
import sys
from setuptools import setup, find_packages

sys.path.insert(0, 'src')
import hatena2rest

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Information Technology",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Programming Language :: Python",
    "Topic :: Internet :: WWW/HTTP :: Site Management",
    "Topic :: Text Processing :: Markup",
    "Topic :: Text Processing :: Markup :: XML",
]

long_description = \
        open(os.path.join("docs","README.rst")).read() + \
        open(os.path.join("docs","HISTORY.rst")).read() + \
        open(os.path.join("docs","TODO.rst")).read()

requires = ['setuptools', 'sphinx', 'tinkerer']

setup(name='hatena2rest',
      version=hatena2rest.__version__,
      description='converting Hatena diary to reST format',
      long_description=long_description,
      author='Kouhei Maeda',
      author_email='mkouhei@palmtb.net',
      url='https://github.com/mkouhei/hatena2rest',
      license=' GNU General Public License version 3',
      classifiers=classifiers,
      packages=find_packages('src'),
      package_dir={'': 'src'},
      data_files = [],
      install_requires=requires,
      extras_require=dict(
        test=[
            'nose',
            'pep8',
            'unittest',
            ],
        ),
      test_suite='nose.collector',
      tests_require=['nose','pep8','unittest'],
      entry_points="""
        [console_scripts]
        htn2rst = hatena2rest.command:main
""",
)
