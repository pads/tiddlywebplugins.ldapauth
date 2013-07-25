import os
from setuptools import setup, find_packages

VERSION = '0.1.2'

setup(
	namespace_packages = ['tiddlywebplugins'],
	name = 'tiddlywebplugins.ldapauth',
	version = VERSION,
	description = 'Allows TiddlyWeb users to Authenticate against an LDAP server.',
	long_description=file(os.path.join(os.path.dirname(__file__), 'README')).read(),
	author = 'Ben Paddock',
	url = 'http://pypi.python.org/pypi/tiddlywebplugins.ldapauth',
	packages = find_packages(exclude=['test']),
	author_email = 'pads@thisispads.me.uk',
	platforms = 'Posix; MacOS X; Windows',
	install_requires = ['tiddlyweb', 'python-ldap'],
	extras_require = {
		'testing': ['pytest', 'httplib2', 'mock', 'wsgi_intercept'],
		'coverage': ['pytest-cov', 'python-coveralls'],
		'style': ['pep8']
	},
	zip_safe = False,
	)
