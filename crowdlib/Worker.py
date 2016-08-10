# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: May 2010
'''

from __future__ import division, with_statement


class Worker( object ):
	def __init__(self, id, amt):
		from crowdlib.utility import is_string
		assert is_string(id), id
		self._id = id
		self._amt = amt

	id = property(lambda self: self._id) # [pylint] access seemingly private member _id : pylint:disable=W0212

	def __repr__(self):
		return self.__class__.__name__ + '("' + self._id + '")'
	__str__ = __repr__

	def send_message(self, subject, message):
		self._amt.notify_worker(self._id, subject, message)

	@property
	def is_blocked(self):
		return self._amt.is_worker_id_blocked(self._id)

	def block(self, reason):
		return self._amt.block_worker_id(self._id, reason)

	def unblock(self, reason=None):
		# Reason cannot be retrieved later.
		return self._amt.unblock_worker_id(self._id, reason)  

	@property
	def reason_blocked(self):
		# Only pulls from DB.  AMT can't provide.
		return self._amt.get_worker_block_reason(self._id)  

	@property
	def hits(self):
		from crowdlib.utility.miscellaneous import GeneratingSequence
		return GeneratingSequence(hit for hit in self._amt.get_hits() if self in hit.workers)
	
	@property
	def hit_types(self):
		from crowdlib.utility.miscellaneous import GeneratingSequence
		return GeneratingSequence(hit_type for hit_type in self._amt.get_hit_types() if self in hit_type.workers)

	@property
	def bonuses_paid(self): 
		from crowdlib.utility.miscellaneous import GeneratingSequence
		return GeneratingSequence(self._amt.get_bonuses(worker_id=self._id))
	

