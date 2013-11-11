#!/usr/bin/env python
# vim: set fileencoding=utf-8:

from setuptools import setup


DESCRIPTION = """Megaplan is a popular Russian CRM, which includes a task
manager among other things.  This module implements parts of the API to work
with the tasks."""


setup(
    author = 'Justin Forest',
    author_email = 'hex@umonkey.net',
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 2",
        "Topic :: Software Development :: Bug Tracking",
    ],
    description = 'Python interface to megaplan.ru API',
    license = 'GNU GPL',
    long_description = DESCRIPTION,
    name = 'megaplan',
    package_dir = {'': 'src'},
    packages = ['megaplan'],
    requires = ['json'],
    url = 'http://code.umonkey.net/python-megaplan/',
    version = '1.4'
)
