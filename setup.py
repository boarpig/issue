#!/usr/bin/python

from distutils.core import setup

with open('README.rst') as file:
    long_description = file.read()

setup(
        name = "issue", 
        version = '0.1',
        description = "Simple issue tracker to use with VCS",
        long_description = long_description,
        author = "Lauri Hakko",
        author_email = "lauri.hakko@gmail.com",
        url = "https://github.com/boarpig/issue",
        classifiers = [
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development',
            'Topic :: Software Development :: Bug Tracking',
            'Topic :: Utilities'
            ]
        )

