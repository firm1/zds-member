#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# https://docs.djangoproject.com/en/dev/intro/reusable-apps/

import os

from pip.download import PipSession
from pip.req import parse_requirements

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

session = PipSession()

setup(
    name='zds-member',
    version='0.1.1',
    packages=['member'],
    include_package_data=True,
    license='GPLv3',
    description='Django user module implemented with Django framework',
    long_description=README,
    url='https://github.com/firm1/zds-member',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    test_suite="runtests.runtests",
    install_requires=[str(pkg.req) for pkg in parse_requirements('requirements-dev.txt', session=session)],
    tests_require=[str(pkg.req) for pkg in parse_requirements('requirements-dev.txt', session=session)],
)
