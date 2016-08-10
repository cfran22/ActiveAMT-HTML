# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: January 2010
'''

from __future__ import division, with_statement
from crowdlib.utility.time_utils import now_local

from datetime import datetime

class Assignment( dict ):
	ASSIGNMENT_STATUS_SUBMITTED = "Submitted"
	ASSIGNMENT_STATUS_APPROVED  = "Approved"
	ASSIGNMENT_STATUS_REJECTED  = "Rejected"

	def __init__(self, id, worker, hit, assignment_status, autopay_time,# [pylint] doesn't call dict.__init__(..) : pylint:disable=W0231
							accept_time, submit_time, approval_time, rejection_time,
							requester_feedback, answers, amt ):
		from crowdlib.HIT import HIT
		from crowdlib.utility import is_unicode, is_string
		from crowdlib.Worker import Worker
		assert is_unicode(id)
		assert isinstance(worker, Worker)
		assert isinstance(hit, HIT)
		assert is_unicode(assignment_status)
		assert isinstance(autopay_time, datetime) or autopay_time is None, autopay_time
		assert isinstance(accept_time, datetime)
		assert isinstance(submit_time, datetime) or submit_time is None
		assert isinstance(approval_time, datetime) or approval_time is None
		assert isinstance(rejection_time, datetime) or rejection_time is None

		self._amt = amt

		self._id = id
		self._worker = worker
		self._hit = hit
		self._assignment_status = assignment_status
		self._autopay_time = autopay_time
		self._accept_time = accept_time
		self._submit_time = submit_time
		self._approval_time = approval_time
		self._rejection_time = rejection_time
		self._answers = answers
		self.update(dict((answer.question_id,answer) for answer in answers))
		self._requester_feedback = requester_feedback
		assert is_string(self._requester_feedback) or self._requester_feedback is None, requester_feedback

		self._last_sync_with_amt_time_secs = None
		self._max_sync_with_amt_secs = 5.0
		self._is_shell = (self._amt is None)

	# [pylint] accessing seemingly private members : pylint:disable=W0212
	id = property(lambda self:self._id)
	worker = property(lambda self: self._worker)
	hit = property(lambda self: self._hit)
	hit_type = property(lambda self: self._hit.hit_type)
	autopay_time = property(lambda self: self._autopay_time)
	accept_time = property(lambda self: self._accept_time)
	submit_time = property(lambda self: self._submit_time)
	requester_feedback = property(lambda self: self._requester_feedback)
	# [pylint] accessing seemingly private members : pylint:enable=W0212

	@property
	def assignment_status(self):
		self._update_approval_if_needed()
		return self._assignment_status

	@property
	def approval_time(self):
		self._update_approval_if_needed()
		return self._approval_time

	@property
	def rejection_time(self):
#		self._update_approval_if_needed()
		return self._rejection_time

	@property
	def review_time(self):
		"Time the assignment was either approved or rejected, or None if it is still pending"
		assignment_status = self.assignment_status
		if assignment_status==self.ASSIGNMENT_STATUS_SUBMITTED:
			return None
		elif assignment_status==self.ASSIGNMENT_STATUS_APPROVED:
			return self._approval_time
		elif assignment_status==self.ASSIGNMENT_STATUS_REJECTED:
			return self._rejection_time

	def _update_approval_if_needed(self):
		now = now_local()
		if self._assignment_status==self.ASSIGNMENT_STATUS_SUBMITTED and self._autopay_time <= now:
#			self._approval_time = now
			self._approval_time = self._autopay_time
			self._assignment_status = self.ASSIGNMENT_STATUS_APPROVED

	def _update_status_from_amt(self, assignment_status, approval_time, rejection_time):
		# THIS WILL BE CALLED BY THE AMT CLASS.
		changed = (self._assignment_status != assignment_status) \
		       or (self._approval_time != approval_time) \
			   or (self._rejection_time != rejection_time)
		self._assignment_status = assignment_status
		self._approval_time = approval_time
		self._rejection_time = rejection_time
		return changed

	@property
	def answers(self):
		return sorted(self._answers)
#		from crowdlib.Dictuple import Dictuple
#		return Dictuple(self._answers, id_fn=lambda ans:ans.question_id)

	@property
	def is_final(self):
		self._update_approval_if_needed()

		if self._assignment_status==self.ASSIGNMENT_STATUS_APPROVED:
			assert self._approval_time is not None
			assert self._rejection_time is None
			return True
		elif self._assignment_status==self.ASSIGNMENT_STATUS_REJECTED:
			assert self._rejection_time is not None
			assert self._approval_time is None
			return True
		else:
			return False

	@property
	def is_paid(self):
		return (self.assignment_status==self.ASSIGNMENT_STATUS_APPROVED)

	@property
	def is_reviewable(self):
		self._update_approval_if_needed()
		return (self.assignment_status==self.ASSIGNMENT_STATUS_SUBMITTED)

	@property
	def is_rejected(self):
		return (self.assignment_status==self.ASSIGNMENT_STATUS_REJECTED)

#	def __getitem__(self,question_id):
#		items = tuple(a for a in self._answers if a.question_id==question_id)
#		assert len(items) >= 0
#		if len(items)==1:
#			return items[0]
#		elif len(items)==0:
#			raise KeyError( "Answer with that question_id not found:  "+str(question_id) )
#		else:
#			assert False, "Shouldn't have multiple answers with same item_id."
#	
#	def keys(self):
#		return sorted(a.question_id for a in self._answers)
#
#	def values(self):
#		return sorted(self._answers, key=lambda a:a.question_id)
#
#	def has_key(self, question_id):
#		return any(a.question_id==question_id for a in self._answers)

	def reject(self, feedback=None):
		from crowdlib.all_exceptions import AssignmentAlreadyFinalizedException

		if self.is_final:
			raise AssignmentAlreadyFinalizedException(self._id, self._assignment_status)

		self._rejection_time = now_local()
		self._amt.reject_assignment(self, feedback, self._rejection_time)
		self._assignment_status = self.ASSIGNMENT_STATUS_REJECTED

	def approve(self, feedback=None):
		from crowdlib.all_exceptions import AssignmentAlreadyFinalizedException

		if self.is_final:
			raise AssignmentAlreadyFinalizedException(self._id, self._assignment_status)

		self._approval_time = now_local()
		self._amt.approve_assignment(self, feedback, self._approval_time)
		self._assignment_status = self.ASSIGNMENT_STATUS_APPROVED

	def grant_bonus(self, amount, reason):
		self._amt.grant_bonus(assignment_id=self._id, worker_id=self._worker.id, amount=amount, currency=None, reason=reason)
	
	@property
	def bonuses_paid(self): 
		return self._amt.get_bonuses(assignment_id=self._id)
	
	@property
	def bonuses_paid_total_amount(self):
		bonuses = tuple(self.bonuses_paid)
		currencies = set(bonus.currency for bonus in bonuses)
		if len(currencies) > 1:
			raise ValueError("There were multiple currencies in these bonuses.  This is not supported.  %s"%(repr(bonuses)))
		assert ((len(bonuses)==0) ^ (len(currencies)==1)), "%s ... %s"%(len(bonuses), len(currencies))
		total_amount = sum(bonus.amount for bonus in bonuses)
		return total_amount

	@property
	def time_spent(self):
		return self.submit_time - self.accept_time

	@property
	def hourly_rate(self):
		# Without regard to whether it was approved or rejected.  Assume it was paid.
		# Returns None if for some reason time were 0.0.  Not sure how that could happen.
		from crowdlib.utility import total_seconds
		hours = float(total_seconds(self.time_spent)) / 60.0 / 60.0  # float(..) is totally unnecessary here.  Just paranoid.
		reward = float(self.hit.hit_type.reward)
		if hours == 0.0:
			return None  # not sure why we'd ever get here, but you never know.
		else:
			return reward/hours

	def __str__(self):
		return "Assignment(id=%s, worker_id=%s, submit_time=%s, ...)"%(
				self.id,
				self.worker.id,
				self.submit_time.strftime("%m/%d/%Y %H:%M:%S"))
	__repr__=__str__
	


