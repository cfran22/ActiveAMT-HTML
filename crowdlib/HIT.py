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
_UNDEFINED = object()

class HIT( object ):
	
	HIT_STATUS_ASSIGNABLE   = "Assignable"
	HIT_STATUS_UNASSIGNABLE = "Unassignable"
	HIT_STATUS_REVIEWABLE   = "Reviewable"
	HIT_STATUS_REVIEWING    = "Reviewing"
	HIT_STATUS_DISPOSED     = "Disposed"
	VALID_HIT_STATUSES = (HIT_STATUS_ASSIGNABLE, HIT_STATUS_UNASSIGNABLE, 
			HIT_STATUS_REVIEWING, HIT_STATUS_REVIEWABLE, HIT_STATUS_DISPOSED)

	HIT_REVIEW_STATUS_NOT_REVIEWED = "NotReviewed"
	HIT_REVIEW_STATUS_MARKED_FOR_REVIEW = "MarkedForReview"
	HIT_REVIEW_STATUS_REVIEWED_APPROPRIATE = "ReviewedAppropriate"
	HIT_REVIEW_STATUS_REVIEWED_INAPPROPRIATE = "ReviewedInappropriate"
	VALID_HIT_REVIEW_STATUSES = (HIT_REVIEW_STATUS_NOT_REVIEWED,
			HIT_REVIEW_STATUS_MARKED_FOR_REVIEW, HIT_REVIEW_STATUS_REVIEWED_APPROPRIATE,
			HIT_REVIEW_STATUS_REVIEWED_INAPPROPRIATE)

	def __init__(self, id, hit_type, question_xml, max_assignments, requester_annotation, 
			creation_time, hit_status, expiration_time,
			num_pending, num_available, num_completed,
			hit_review_status, approximate_expiration_time, amt):
		from crowdlib.utility import to_unicode

		self._id = to_unicode(id)
		self._hit_type = hit_type
		self._requester_annotation = to_unicode(requester_annotation)
		self._max_assignments = max_assignments
		self._creation_time=creation_time
		self._hit_status=hit_status
		assert self._hit_status in self.VALID_HIT_STATUSES, (self._hit_status, self.VALID_HIT_STATUSES)
		self._expiration_time=expiration_time
		self._num_pending=num_pending
		self._num_available=num_available
		self._num_completed=num_completed
		self._hit_review_status = hit_review_status
		self._approximate_expiration_time = approximate_expiration_time

		if isinstance(self._hit_review_status,str):
			self._hit_review_status = to_unicode(self._hit_review_status)

		if (self._hit_review_status not in self.VALID_HIT_REVIEW_STATUSES) and (self._hit_review_status is not None):
			raise ValueError( "Unexpected HIT Review Status.  %s should be in %s."%(
				repr(self._hit_review_status), repr(self.VALID_HIT_REVIEW_STATUSES)))

		self._question_xml=to_unicode(question_xml)
		self._amt = amt

	id = property(lambda self: self._id)                                     # [pylint] access private member : pylint:disable=W0212
	hit_type = property(lambda self: self._hit_type)                         # [pylint] access private member : pylint:disable=W0212
	requester_annotation = property(lambda self: self._requester_annotation) # [pylint] access private member : pylint:disable=W0212
	creation_time = property(lambda self: self._creation_time)               # [pylint] access private member : pylint:disable=W0212
	hit_review_status = property(lambda self: self._hit_review_status)       # [pylint] access private member : pylint:disable=W0212
	question_xml = property(lambda self: self._question_xml)                 # [pylint] access private member : pylint:disable=W0212
	approximate_expiration_time = property(lambda self:self._approximate_expiration_time)        # [pylint] access private member : pylint:disable=W0212
	autopay_time = property(lambda self:(self.creation_time + self.hit_type.autopay_delay))

	num_submitted = property(lambda s: s.max_assignments - s.num_available - s.num_pending)

	@property
	def _is_final(self):
		return (self._num_completed == self._max_assignments)

	@property
	def num_pending(self):
		"""
		"The number of assignments for this HIT that have been accepted by Workers, but
		have not yet been submitted, returned, abandoned." according to...
		http://docs.amazonwebservices.com/AWSMechTurk/2008-08-02/AWSMturkAPI/ApiReference_HITDataStructureArticle.html
		"""
		self._suggest_sync_with_amt_assignment_counts_if_needed()
		return self._num_pending

	@property
	def num_completed(self):
		"""
		"The number of assignments for this HIT that have been approved or rejected." according to...
		http://docs.amazonwebservices.com/AWSMechTurk/2008-08-02/AWSMturkAPI/ApiReference_HITDataStructureArticle.html
		"""
		self._suggest_sync_with_amt_assignment_counts_if_needed()
		return self._num_completed

	@property
	def num_available(self):
		"""
		"The number of assignments for this HIT that are available for Workers to accept" according to...
		http://docs.amazonwebservices.com/AWSMechTurk/2008-08-02/AWSMturkAPI/ApiReference_HITDataStructureArticle.html
		"""
		self._suggest_sync_with_amt_assignment_counts_if_needed()
		return self._num_available

	@property
	def hit_status(self):
		self._suggest_sync_with_amt_assignment_counts_if_needed()
		assert self._hit_status in self.VALID_HIT_STATUSES, self._hit_status
		return self._hit_status

	@property
	def num_reviewable(self):
		return (self.max_assignments - self.num_pending - self.num_available - self.num_completed)

	def _get_is_available(self):
		if self._hit_status==self.HIT_STATUS_ASSIGNABLE:
			self._amt.suggest_hit_sync(hit_type_id=self.hit_type.id)
		if self._hit_status==self.HIT_STATUS_ASSIGNABLE:
			return True
		else:
			return False
	
	def _set_is_available(self, val):    # pylint: disable=E0102
		if val==False:
			# 4/7/2016:  This test was removed because in some cases, an available hit
			#            is not Assignable because all available assignments are pending.
			#            In other words, workers are working on it.  It seems possible
			#            that this might lead to errors from the AMT server due if the
			#            HIT is already expired.  In that case, we might need to wrap
			#            this in a try block.
			#if self.hit_status==self.HIT_STATUS_ASSIGNABLE:
			#	self._amt.force_expire_hit(self)
			self._amt.force_expire_hit(self) # >>>> Please TELL ALEX IF THIS CAUSES AN EXCEPTION. (code 26215) <<<<
		else:
			raise ValueError("To revive a HIT, use hit.max_assignments or hit.expiration_time.  You need to specify how you want it revived.")
			# Should we just allow it to be revived using the user's defaults?
	
	is_available = property(_get_is_available, _set_is_available) # setter syntax is not supported in Python 2.5
	del _get_is_available, _set_is_available

	def _suggest_sync_with_amt_assignment_counts_if_needed(self):
		from crowdlib.utility import total_seconds
		not_final = (not self._is_final==True)
		at_least_10_seconds_since_hit_created = (total_seconds(now_local() - self.creation_time) > 10)
		if not_final and at_least_10_seconds_since_hit_created:
			self._amt.suggest_hit_sync(hit_type_id=self.hit_type.id)
			#self._amt.sync_with_amt()
	
	def _set_force_expired_from_amt(self, approximate_expiration_time): # NOT PRIVATE - WILL BE CALLED BY AMT CLASS
		# When we call ForceExpireHIT, the server doesn't report the exact Expiration that the HIT
		# has after the operation.  We don't want to confuse the official server value with
		# our local time, so we will store the approximate value separately.

		assert approximate_expiration_time is not None
		# Tested on 12/7/2013.  The only effect on the HIT structure of ForceExpireHIT or ExtendHIT
		# is on the hit status and the expiration time.  num_available and num_pending are not changed.
		#
		# After ForceExpireHIT, if there were no pending assignments, status becomes reviewable (even if nothing was ever submitted)
		# and num_available remains the same.  It is perfectly possible to have num_available >= 1 even for a HIT that is expired.
		#
		# If there was a pending assignment, status becomes unassignable.  Once the pending assignment is submitted, the status
		# changes to reviewable.
		#

		changes = {}

		if approximate_expiration_time != self._approximate_expiration_time:
			self._approximate_expiration_time = approximate_expiration_time
			changes["approximate_expiration_time"] = approximate_expiration_time

		if self._hit_status == HIT.HIT_STATUS_ASSIGNABLE:
			if self._num_pending == 0:
				self._hit_status = HIT.HIT_STATUS_REVIEWABLE
			else:
				self._hit_status = HIT.HIT_STATUS_UNASSIGNABLE
			changes["hit_status"] = self._hit_status

		return changes

	def _update_from_amt_due_to_extend_hit(self, expiration_increment, max_assignments_increment): # NOT PRIVATE - WILL BE CALLED BY AMT CLASS
		# When we call ExtendHIT, the server doesn't report the exact Expiration that the HIT
		# has after the operation.  We don't want to confuse the official server value with
		# our local time, so we will store the approximate value separately.
		changes = {}

		if max_assignments_increment > 0:
			self._max_assignments += max_assignments_increment
			changes["max_assignments"] = self._max_assignments

		if expiration_increment > 0:
			# From the docs:
			#
			# "The amount of time, in seconds, by which to extend the
			# expiration date. If the HIT has not yet expired, this amount is
			# added to the HIT's expiration date. If the HIT has expired, the
			# new expiration date is the current time plus this value."
			#
			# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_ExtendHITOperation.html
			import datetime
			td = datetime.timedelta(seconds=expiration_increment)

			if self._approximate_expiration_time is None:
				ref = self._expiration_time
			else:
				ref = self._approximate_expiration_time

			ref = max(ref, now_local())

			self._approximate_expiration_time = ref + td
			changes["approximate_expiration_time"] = self._approximate_expiration_time

		if self._hit_status != HIT.HIT_STATUS_ASSIGNABLE:
			self._hit_status = HIT.HIT_STATUS_ASSIGNABLE
			changes["hit_status"] = self._hit_status

		return changes

	def _update_from_amt(self, expiration_time, max_assignments, num_pending, num_available, num_completed, hit_status, question_xml, approximate_expiration_time): # NOT PRIVATE - WILL BE CALLED BY AMT CLASS

		# WARNING:  max_assignments from server might not be accurate.  (see note near top of AMTServer)

		changed = False

		if self._expiration_time != expiration_time:
			self._expiration_time = expiration_time
			changed = True
#			_dbg_log_20131120(self._id + " : _expiration_time changed")

		if self._max_assignments != max_assignments:
			self._max_assignments = max_assignments
			changed = True
#			_dbg_log_20131120(self._id + " : _max_assignments changed")

		if self._num_pending != num_pending:
			self._num_pending = num_pending
			changed = True
#			_dbg_log_20131120(self._id + " : _num_pending changed")

		if self._num_available != num_available:
			self._num_available = num_available
			changed = True
#			_dbg_log_20131120(self._id + " : _num_available changed")

		if self._num_completed != num_completed:
			self._num_completed = num_completed
			changed = True
#			_dbg_log_20131120(self._id + " : _num_completed changed")

		if self._hit_status != hit_status:
#			_dbg_log_20131120(self._id + " : _hit_status changed from %r to %r"%(self._hit_status, hit_status))
			self._hit_status = hit_status
			changed = True

		if (self._question_xml != question_xml) and (question_xml is not None) and (len(question_xml)>10):
			self._question_xml = question_xml
			changed = True
#			_dbg_log_20131120(self._id + " : ._question_xml changed")

		if (self._approximate_expiration_time != approximate_expiration_time):
			self._approximate_expiration_time = approximate_expiration_time
			changed = True
#			_dbg_log_20131120(self._id + " : ._question_xml changed")

		return changed

	@property
	def assignments(self):
		from crowdlib.utility.miscellaneous import GeneratingSequence
		return GeneratingSequence(self._amt.get_assignments_for_hit(self))

	max_assignments = property(lambda self: self._max_assignments)           # [pylint] access private member : pylint:disable=W0212

	def _get_max_assignments(self):
		return self._max_assignments

	def _set_max_assignments(self, val):    # pylint: disable=E0102
		# WARNING:  max_assignments from server might not be accurate.  (see note near top of AMTServer)

		max_assignments_increment = int(val - self._max_assignments)
		if max_assignments_increment < 0:
			raise ValueError( "You cannot decrease max_assignments." )
		elif max_assignments_increment == 0:
			pass # noop
		else:
			self._amt.extend_hit(self, max_assignments_increment=max_assignments_increment)
			self._max_assignments = val
			self._hit_status = self.HIT_STATUS_ASSIGNABLE
			#FIXME:  If the HIT is expired, then this status will be wrong! (ref#7020)
	
	max_assignments = property(_get_max_assignments, _set_max_assignments) # setter syntax is not supported in Python 2.5
	del _get_max_assignments, _set_max_assignments
	
	@property
	def average_time_taken(self):
		# Excludes rejected work but includes work not yet approved/rejected.
		from crowdlib.utility import to_duration, total_seconds
		total_secs = 0.0
		total_non_rejected_assignments = 0
		for asg in self.assignments:
			if not asg.is_rejected:
				total_secs += float(total_seconds(asg.time_spent)) # float(..) probably unnecessary... paranoid.
				total_non_rejected_assignments += 1
		if total_non_rejected_assignments==0:
			return None
		else:
			return to_duration(total_secs / float(total_non_rejected_assignments))
	
	@property
	def hourly_rate(self):
		from crowdlib.utility import total_seconds
		# Excludes rejected work but includes work not yet approved/rejected.
		total_secs = 0.0
		total_non_rejected_assignments = 0
		for asg in self.assignments:
			if not asg.is_rejected:
				total_secs += float(total_seconds(asg.time_spent)) # float(..) probably unnecessary... paranoid.
				total_non_rejected_assignments += 1
		if total_non_rejected_assignments==0:
			return None
		else:
			return (self.hit_type.reward * total_non_rejected_assignments) / (total_secs / 60.0 / 60.0)
	
	def _get_expiration_time(self):
		if self._approximate_expiration_time:
			self._amt.suggest_hit_sync(hit_type_id=self.hit_type.id, must_sync=True)
		return self._expiration_time

	def _set_expiration_time(self, val):
		from crowdlib.utility import to_date_time, total_seconds, to_local_if_naive
		val = to_date_time(val)
		val = to_local_if_naive(val)
		expiration_increment = total_seconds(val - now_local())
		if expiration_increment < 3600:
			raise ValueError( "You may only increase the expiration_time, and only by at least 1 hour." )
		else:
			self._amt.extend_hit(self, expiration_increment=expiration_increment)
			self._expiration_time = val
			self._hit_status = self.HIT_STATUS_ASSIGNABLE
			#FIXME:  If there are no more available assignments, then this status will be wrong! (ref#9519)

	expiration_time = property(_get_expiration_time, _set_expiration_time) # setter syntax is not supported in Python 2.5
	del _get_expiration_time, _set_expiration_time

	@property
	def answers(self):  # GENERATOR
		from crowdlib.utility.miscellaneous import GeneratingSequence
		return GeneratingSequence(answer for assignment in self.assignments
			                             for answer in assignment.answers)
	
	@property
	def workers(self):  # GENERATOR
		from crowdlib.utility.miscellaneous import GeneratingSequence
		return GeneratingSequence(self._get_workers())
	
	def _get_workers(self):
		worker_ids_seen_so_far = set()
		for assignment in self.assignments:
			worker = assignment.worker
			worker_id = worker.id
			if worker_id not in worker_ids_seen_so_far:
				worker_ids_seen_so_far.add(worker_id)
				yield worker

	def __repr__(self):
		return self.__class__.__name__+repr((self.id,
											 self.max_assignments,
											 self.requester_annotation,
											 self.hit_status))
	
#def _dbg_log_20131120(*args, **kwargs):
#	# This was for temporary debugging on 11/20/2013.
#	# I'm leaving it in for now (as of 12/1/2013) until I'm positive the bug is definitely gone.
#	import os
#	if "DEBUGGING_20131120" in os.environ:
#		from crowdlib.utility import log
#		log(*args, **kwargs)

if __name__=="__main__":
	import sys
	sys.stderr.write( "\nThis is just a module, not the code entry point.\n" )
