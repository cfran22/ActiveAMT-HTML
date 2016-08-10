# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: April 2011
'''

from __future__ import division, with_statement

class Bonus(object):
	def __init__(self, assignment_id, worker_id, amount, currency, payment_time, reason, amt):
		self._assignment_id = assignment_id
		self._worker_id = worker_id
		self.amount = amount
		self.currency = currency
		self.payment_time = payment_time
		self.reason = reason
		self._amt = amt
	
	@property
	def assignment(self):
		return self._amt.get_assignment(self._assignment_id)
	
	@property
	def worker(self):
		return self._amt.get_assignment(self._worker_id)

	def __str__(self):
		s = "Bonus: %.2f t=%s, w=%s a=%s r=%s"%(
				self.amount,
				self.payment_time,
				self._worker_id,
				self._assignment_id,
				repr(self.reason)
		)
		return s
	
	def __repr__(self):
		parts = (self._assignment_id, self._worker_id, self.amount, self.currency, self.payment_time, self.reason)
		s = "Bonus(" + ", ".join(map(str,parts)) + ")"
		return s
