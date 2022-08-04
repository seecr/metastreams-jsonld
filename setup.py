#!/usr/bin/env python3
## begin license ##
#
# "Metastreams Json LD" provides utilities for handling json-ld data structures
#
# Copyright (C) 2022 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Metastreams Json LD"
#
# "Metastreams Json LD" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Metastreams Json LD" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Metastreams Json LD"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here/"README.md").read_text(encoding="utf-8")

version='0.1.0'

packages=find_packages(exclude=('metastreams',))
packages=find_packages() #DO_NOT_DISTRIBUTE

setup(
    name='metastreams-jsonld',
    version=version,
    description='Json-ld utilities',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=packages,
    author='Seecr',
    author_email='info@seecr.nl',
    url='https://github.com/seecr/metastreams',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
    ],
)

