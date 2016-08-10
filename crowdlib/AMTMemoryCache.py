# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: January 2011
'''

from __future__ import division, with_statement

_USE_WEAKREF_FOR_ASSIGNMENTS = True # reenabled on 12/3/2013

class AMTMemoryCache(object):

	def __init__(self):
		import weakref

		self._hit_dict = {}
		self._hit_type_dict = {}
		self._worker_dict = {}
		if _USE_WEAKREF_FOR_ASSIGNMENTS:
			self._assignment_dict = weakref.WeakValueDictionary()
		else:
			self._assignment_dict = {}  # disabled weakref 8-20-2011 for debugging; reenabled on 12/3/2013

	
	#############################################
	# WORKER

	def has_worker(self, worker_id):
		return (worker_id in self._worker_dict)

	def put_worker(self, worker):
		from crowdlib.all_exceptions import CrowdLibInternalError
		if self.has_worker(worker.id):
			raise CrowdLibInternalError("Worker %s already exists in memory cache."%worker.id)
		self._worker_dict[worker.id] = worker
	
	def get_worker(self, worker_id):
		from crowdlib.all_exceptions import WorkerNotFoundException
		try:
			return self._worker_dict[worker_id]
		except KeyError:
			raise WorkerNotFoundException(worker_id, "Worker %s not found in memory cache"%worker_id)

	def get_worker_ids(self):
		return sorted(self._worker_dict.keys())


	#############################################
	# HIT_TYPE

	def has_hit_type(self, hit_type_id):
		return (hit_type_id in self._hit_type_dict)

	def put_hit_type(self, hit_type):
		from crowdlib.all_exceptions import CrowdLibInternalError
		if self.has_hit_type(hit_type.id):
			raise CrowdLibInternalError("HITType %s already exists in memory cache."%(hit_type.id))
		self._hit_type_dict[hit_type.id] = hit_type
	
	def get_hit_type(self, hit_type_id):
		from crowdlib.all_exceptions import HITTypeNotFoundException
		try:
			return self._hit_type_dict[hit_type_id]
		except KeyError:
			raise HITTypeNotFoundException(hit_type_id, "HITType %s not found in memory cache."%hit_type_id)

	def get_hit_type_ids(self):
		return sorted(self._hit_type_dict.keys())


	#############################################
	# HIT

	def has_hit(self, hit_id):
		return (hit_id in self._hit_dict)

	def put_hit(self, hit):
		from crowdlib.all_exceptions import CrowdLibInternalError
		if self.has_hit(hit.id):
			raise CrowdLibInternalError("HIT %s already exists in memory cache."%(hit.id))
		self._hit_dict[hit.id] = hit
	
	def get_hit(self, hit_id):
		from crowdlib.all_exceptions import HITNotFoundException
		try:
			return self._hit_dict[hit_id]
		except KeyError:
			raise HITNotFoundException(hit_id, "HIT %s not found in memory cache"%hit_id)

	def get_hit_ids(self):
		return sorted(self._hit_dict.keys())


	#############################################
	# ASSIGNMENT

	# has_assignment is omitted intentionally to avert the possibility of a bug where you do...
	#        if self._memory_cache.has_assignment(asg_id):
	#            asg = self._memory_cache.get_assignment(asg_id)
	# ... and find that it has been garbage collected between the two statements.  This
	# is only an issue because this uses a weakref structure.

	def put_assignment(self, assignment):
		from crowdlib.all_exceptions import CrowdLibInternalError
		if assignment.id in self._assignment_dict:
			raise CrowdLibInternalError("Assignment %s already exists in memory cache."%(assignment.id))
		self._assignment_dict[assignment.id] = assignment
	
	def get_assignment(self, assignment_id):
		from crowdlib.all_exceptions import AssignmentNotFoundException
		try:
			return self._assignment_dict[assignment_id]
		except KeyError:
			raise AssignmentNotFoundException(assignment_id, "Assignment %s not found in memory cache"%assignment_id)
	
	def get_assignments_for_hit_id(self, hit_id):
		if _USE_WEAKREF_FOR_ASSIGNMENTS:
			assignment_refs = self._assignment_dict.itervaluerefs()  # iterable
			assignments = (assignment_ref() for assignment_ref in assignment_refs)  # iterable, generator
		else:
			try:
				# Python 2
				assignments = self._assignment_dict.itervalues()
			except AttributeError:
				# Python 3
				assignments = self._assignment_dict.values()
		assignments = tuple(asg for asg in assignments if (asg is not None) and (asg.hit.id==hit_id))
		return assignments


if __name__=="__main__":
	import sys
	sys.stderr.write( "\nThis is just a module, not the code entry point.\n" )