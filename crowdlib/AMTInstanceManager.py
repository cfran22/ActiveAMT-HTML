# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: December 2013
'''
from __future__ import division, with_statement
import threading
from crowdlib.utility import to_unicode
from crowdlib.AMT import AMT

_ONE_INSTANCE_PER_THREAD = False

class AMTInstanceManager(object):
	def __init__(self):
		self._instances_dict = {}

	def get_amt(self, settings):
		# Return same instance for any unique set of settings plus, optionally, the current thread ID.

		instance_key = [(k,v) for (k,v) in vars(settings).items() if not k.startswith("_")]
		instance_key.sort()
		if _ONE_INSTANCE_PER_THREAD:
			thread_ident = threading.current_thread().ident
			instance_key.insert(0, thread_ident)
		instance_key = to_unicode(instance_key)

		try:
			amt = self._instances_dict[instance_key]
		except KeyError:
			amt = AMT(settings)
			self._instances_dict[instance_key] = amt

		return amt