# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alex Quinn
@contact: aq@cs.umd.edu
@since: January 2010
'''

from __future__ import division, with_statement

import sys, time
_g_last_line_length = 0

def log(s, should_terminate=True, flag=None):
	prefix = "# %s  "%time.strftime("%H:%M:%S")
	if flag:
		prefix += flag + "  "
	s = prefix + s
	if _g_last_line_length > 0:
		s = "\n" + s
	if should_terminate:
		s += "\n"
	dmp(s)

def dmp(s):
	global _g_last_line_length # [pylint] using global statement : pylint:disable=W0603
	last_nl = s.rfind("\n")
	assert last_nl >= s.rfind("\r")
	_g_last_line_length = len(s) - last_nl - 1
	sys.stdout.flush()
	sys.stderr.flush()
	sys.stderr.write(s)
	sys.stderr.flush()

def clear_line():
	global _g_last_line_length # [pylint] using global statement : pylint:disable=W0603
	sys.stdout.flush()
	sys.stderr.flush()
	sys.stderr.write("\x08"*_g_last_line_length + " "*_g_last_line_length + "\x08"*_g_last_line_length)
	sys.stderr.flush()
	_g_last_line_length = 0
