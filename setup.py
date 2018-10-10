#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

#
# Grab some info from supporting files
#
with open('README.md', 'r') as fh:
    long_description = fh.read()

from pigskin.__version__ import VERSION
__version__ = '.'.join(map(str, VERSION))

#
# Provide a little info about who we are
#
setuptools.setup(
    name = 'pigskin',
    version = __version__,
    author = 'Alex Waite and many others',
    author_email = 'alex@waite.eu',
    description = 'A Python library for NFL Game Pass',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/aqw/pigskin',
    license = 'MIT',
    classifiers = [
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
    ],
    python_requires = ">2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    packages = setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires = [
        'requests',
        'm3u8',
    ],
    tests_require = [
        'pyflakes',
        'pytest',
        'vcrpy',
    ],
)
