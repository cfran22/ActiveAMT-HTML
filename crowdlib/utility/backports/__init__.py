# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alex Quinn
@contact: aq@cs.umd.edu
@since: December 2013
'''

from __future__ import division, with_statement

try:
	from ast import literal_eval
except ImportError:
	from crowdlib.utility.backports.literal_eval import literal_eval

try:
	from collections import namedtuple
except ImportError:
	from crowdlib.utility.backports.namedtuple import namedtuple

try:
	from inspect import getcallargs
except ImportError:
	from crowdlib.utility.backports.getcallargs import getcallargs
