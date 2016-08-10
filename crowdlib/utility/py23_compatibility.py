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

def urlencode_py23_compatible(query, doseq=False):
	try:
		# Python 2
		urlencode_fn = __import__("urllib", fromlist=("urlencode",)).urlencode
	except AttributeError:
		# Python 3
		urlencode_fn = __import__("urllib.parse", fromlist=("urlencode",)).urlencode

	return urlencode_fn(query=query, doseq=doseq)

def urlopen_py23_compatible(url, data=None, timeout=None):
	try:
		# Python 2
		urlopen_fn = __import__("urllib", fromlist=("urlopen",)).urlopen
	except AttributeError:
		# Python 3
		urlopen_fn = __import__("urllib.request", fromlist=("urlopen",)).urlopen

	# The data, if any, must either be bytes (Python 3) or a str or unicode made of characters
	# that can be encoded as ASCII.  In other words, it may not contain any
	# non-ASCII characters.  Python 3.2 enforces that data must be a bytes object.
	if data is not None and hasattr(data, "encode"):
		data = data.encode("ascii", "strict")
		# Python 2:  data is now a str
		# Python 3:  data is now a bytes

	if timeout is None:
		return urlopen_fn(url=url, data=data)
	else:
		return urlopen_fn(url=url, data=data, timeout=timeout)

def urlretrieve_py23_compatible(url, filename=None, reporthook=None, data=None):
	try:
		# Python 2
		urlretrieve_fn = __import__("urllib", fromlist=("urlretrieve",)).urlretrieve
	except AttributeError:
		# Python 3
		urlretrieve_fn = __import__("urllib.request", fromlist=("urlretrieve",)).urlretrieve

	return urlretrieve_fn(url=url, filename=filename, reporthook=reporthook, data=data)

def base64_encodestring_py23_compatible(s):
	try:
		# Python 3
		base64_encodestring = __import__("base64", fromlist=("encodebytes",)).encodebytes
	except AttributeError:
		# Python 2
		base64_encodestring = __import__("base64", fromlist=("encodestring",)).encodestring

	return base64_encodestring(s)




