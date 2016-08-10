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


def launch_url_in_browser_if_possible(url):
	# FAIL SILENTLY
	import os, sys
	try:
		if sys.platform=="darwin":	# If this is Mac OS X
			os.system( "start \"%s\""%url )
		else:
			os.startfile( url )
	except:
		pass

def total_seconds(duration):
	# Input:   timedelta object
	# Output:  integer number of seconds
	#
	# This function does almost the same thing as timedelta.total_seconds(..) except that:
	# - It works on Python 2.6 and 3.1.  timedelta.total_seconds(..) wasn't introduced until 2.7 and 3.2.
	# - It truncates any microseconds.
	return duration.seconds + (duration.days * 24 * 60 * 60)

def poll(duration, interval, callback_fn, callback_args=(), callback_kwargs=None):
	from crowdlib.utility.type_utils import to_duration
	import time
	callback_kwargs = callback_kwargs if callback_kwargs is not None else {} # avoid passing in unsafe {}
	duration_secs = total_seconds(to_duration(duration))
	interval_secs = total_seconds(to_duration(interval))
	time_limit = time.time() + duration_secs
	while True:
		start_time = time.time()
		callback_fn(*callback_args, **callback_kwargs)
		end_time = time.time()
		elapsed_time = (end_time - start_time)
		time_to_sleep = interval_secs - elapsed_time
		if end_time >= time_limit:
			break
		elif time_to_sleep > 0:
			time.sleep(time_to_sleep) # sleep takes seconds, not milliseconds!

class GeneratingSequence(object): # [pylint] doesn't implement __delitem__ or __setitem__ : pylint:disable=R0924
	def __init__(self, iterable):
		from crowdlib.utility.type_utils import is_sequence
		if is_sequence(iterable):
			if isinstance(iterable, tuple):
				self._sequence = iterable
			else:
				self._sequence = tuple(iterable)
			self._is_filled = True
			self._source_iterator = None
		else:
			self._sequence = []
			self._is_filled = False
			self._source_iterator = iter(iterable)
		self._next_idx = 0
	
	def __iter__(self):
		if self._is_filled:
			return iter(self._sequence)
		else:
			return self

	def _fill(self):
		if not self._is_filled:
			self._sequence.extend(self._source_iterator)
			self._source_iterator = None
			self._is_filled = True
	
	def next(self):
		try:
			element = self._sequence[self._next_idx]
		except IndexError:
			if self._is_filled:
				raise StopIteration
			else:
				element = next(self._source_iterator) # might raise StopIteration
				self._sequence.append(element)
		self._next_idx += 1
		return element

	def _get_full_sequence(self):
		if not self._is_filled:
			self._fill()
		return self._sequence

	def __getitem__(self, x):
		return self._get_full_sequence().__getitem__(x)

	def count(self, x):
		return self._get_full_sequence().count(x)

	def index(self, x):
		return self._get_full_sequence().index(x)

	def __len__(self):
		return len(self._get_full_sequence())

	def __repr__(self):
		s = repr(self._get_full_sequence())
		if s[0] == "[" and s[-1] == "]":
			s = "(" + s[1:-1] + ")"
		assert s[0] == "(" and s[-1] == ")"
		return s

	def __contains__(self, x):
		return x in self._get_full_sequence()

	

# [no longer used as far as I know, 12/4/2013]
#def switch_to_current_code_directory():
#	import os.path
#	# Switch to same directory as this source code.
#	this_dir = os.path.dirname(__file__)
#	os.chdir( (this_dir if this_dir!="" else "\\") )

# [no longer used as far as I know, 12/4/2013]
#def get_hostname():
#	import os
#	if "COMPUTERNAME" in os.environ:  # Windows
#		hostname = os.environ["COMPUTERNAME"]
#	elif "HOSTNAME" in os.environ:	  # Linux
#		hostname = os.environ["HOSTNAME"]
#	hostname = hostname.lower()
#	return hostname

# [no longer used as far as I know, 12/4/2013]
#def round_up_to_multiple( n, multiple_of ):
#	import math
#	return int( math.ceil( float(n) / multiple_of  ) * multiple_of )

# [no longer used as far as I know, 12/4/2013]
#def get_crowdlib_dir():
#	import os.path
#	return os.path.abspath( os.path.dirname(__file__) )

# [no longer used as far as I know, 12/4/2013]
#def running_as_cgi():
#	import os
#	return "HTTP_HOST" in os.environ

# [no longer used as far as I know, 12/4/2013]
#def set_clipboard_text(s):
#	# Windows only, requires pywin32
#	# http://sourceforge.net/projects/pywin32/
#	import win32clipboard
#	win32clipboard.OpenClipboard()
#	win32clipboard.EmptyClipboard()
#	win32clipboard.SetClipboardText(s)
#	win32clipboard.CloseClipboard()

# [no longer used as far as I know, 12/4/2013]
#def confirm(msg):
#	while True:
#		s = raw_input(msg + " (y/n)  " )
#		if len(s)>0:
#			if s[0].lower() in ("y","yes"):
#				return True
#			elif s[0].lower() in ("n","no"):
#				return False


# [no longer used as far as I know, 12/4/2013]
#def as_generating_sequence(fn): # DECORATOR
#	def _as_generating_sequence(*args, **kwargs):
#		return GeneratingSequence(fn(*args, **kwargs))
#	return _as_generating_sequence
