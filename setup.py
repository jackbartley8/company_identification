#!/usr/bin/env python

from setuptools import setup, find_packages

import os
# import sys
import textwrap

ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name='company_identification',
    version='0.1',
    author='Jack Bartley',
    packages=find_packages(),
    url='https://github.com/jackbartley8/company_identification',
    description=(
        "jacks use only"
        " yo"
    ),
    long_description=textwrap.dedent(
        open(os.path.join(ROOT, 'README.rst')).read()),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
    "requests>=2.23.0"
    ]
)
