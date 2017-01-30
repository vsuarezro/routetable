from distutils.core import setup
setup(
    name = 'routetable',
    packages = ['routetable', 'parsers', 'tests'],
    version = '1.0',
    description = 'Multivendor Route table log comparison',
    author='Victor Suarez',
    author_email='victor.suarez@nokia.com', 
    license='LGPL',
    url='github.com',
    keywords="""Metadata-Version: 1.1, Name: RouteTable, 
    Version: 1.0, Platform: Windows, Linux, 
    Summary: A module to parse and compare route table information, 
    Author: Victor Suarez, Author-email: victor.suarez@nokia.com ,
    License: LGPL, Classifier: Development Status:: Beta,
    Classifier: Programming Language :: Python,
    Classifier: Programming Language :: Python :: 3,
    Classifier: Intended Audience :: Network administrators,
    Requires: re, Requires: os, Requires: sys, Requires: pyqt5 (>=5.7)"""
)


