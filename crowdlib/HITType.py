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

import crowdlib
import crowdlib.utility
import re
import sys
from crowdlib.all_exceptions import AMTRequestFailed, QuestionXMLError
from crowdlib.utility import is_iterable, is_string, launch_url_in_browser_if_possible, to_duration, to_unicode, total_seconds, xml2dom
from crowdlib.utility.miscellaneous import GeneratingSequence
from crowdlib.utility.time_utils import now_local


class HITType( object ):
	# According to the Amazon documentation, the basic information that defines a HITType is:
	#  - Title
	#  - Description
	#  - Reward  (amount and currency type)
	#  - AssignmentDurationInSeconds
	#  - Keyword(s)
	#  - AutoApprovalDelayInSeconds
	#  - QualificationRequirement(s)
	#
	# Thus, if you submit the same parameters, you'll get back the same HITType object with the same ID.
	#
	# See:  RegisterHITType, in Amazon Mechanical Turk API documentation
	#       http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/ApiReference_RegisterHITTypeOperation.html

	def __init__( self,
				  id,
				  title,
				  description,
				  reward,
				  currency,
				  time_limit,
				  autopay_delay,
				  keywords,
				  qualification_requirements,
				  amt
				  ):

		self._id = to_unicode(id)
		self._title = to_unicode(title)
		self._description = to_unicode(description)
		self._reward = reward
		self._currency = to_unicode(currency)
		self._time_limit = time_limit
		self._autopay_delay = autopay_delay
		self._qualification_requirements = qualification_requirements
		self._keywords = keywords
		self._amt = amt # Private AMT reference for doing operations on this HITType instance.

	# [pylint] accessing seemingly private members of self : pylint:disable=W0212
	id          = property(lambda self: self._id, doc="string")
	title       = property(lambda self: self._title, doc="string")
	description = property(lambda self: self._description, doc="string")
	reward      = property(lambda self: self._reward, doc="number")
	currency    = property(lambda self: self._currency, doc="string, ISO 4217 currency code")
	time_limit = property(lambda self: self._time_limit, doc="timedelta")
	autopay_delay = property(lambda self: self._autopay_delay, doc="timedelta")
	qualification_requirements = property(lambda self: self._qualification_requirements, doc="list of QualificationRequirement")
	keywords    = property(lambda self: self._keywords, doc="list of string")
	# [pylint] REENABLE error for accessing private members : pylint:enable=W0212

	@property
	def hits(self):
		return GeneratingSequence(self._amt.get_hits_for_hit_type(self))

	@property
	def assignments(self):
		return GeneratingSequence(assignment for hit in self.hits for assignment in hit.assignments)

	@property
	def answers(self):
		return GeneratingSequence(answer for hit in self.hits
				                         for assignment in hit.assignments
										 for answer in assignment.answers)
	
	@property
	def workers(self):
		return GeneratingSequence(self._get_workers())
	
	def _get_workers(self):
		worker_ids_seen_so_far = set()
		for hit in self.hits:
			for assignment in hit.assignments:
				worker = assignment.worker
				worker_id = worker.id
				if worker_id not in worker_ids_seen_so_far:
					worker_ids_seen_so_far.add(worker_id)
					yield worker

	def _get_is_available(self):
		return any(hit.is_available for hit in self.hits)
	
	def _set_is_available(self, val):
		for hit in self.hits:
			hit.is_available = val

	is_available = property(_get_is_available, _set_is_available) # setter syntax is not supported in Python 2.5
	del _get_is_available, _set_is_available

	@property
	def preview_url(self):
		return self._amt.url_for_hit_type_id(self.id)

	@property
	def reviewable_hits(self):
		return self._amt.get_reviewable_hits(self)
		
	def preview_in_browser(self):
		url = self.preview_url
		launch_url_in_browser_if_possible(url)
	
	def _get_notification_address(self):
		return self._amt.get_hit_type_notification_address(self.id)

	def _set_notification_address(self, url):
		self._amt.set_hit_type_notification_address(self.id, url)
	
	notification_address = property(_get_notification_address, _set_notification_address) # setter syntax is not supported in Python 2.5
	del _get_notification_address, _set_notification_address

	def send_test_notification(self, event_type=None):
		if event_type is None:
			from crowdlib.AMTServer import AMTServer
			event_type = AMTServer.NOTIFICATION_EVENT_TYPE_SUBMITTED
		return self._amt.send_test_notification(address=self.notification_address, event_type=event_type)

	def create_hit(self, *args, **kwargs):
		
		if len(args)==0:
			# Only keyword args received
			maybe_url    = ("url" in kwargs)
			maybe_fields = ("fields" in kwargs)
			maybe_html   = ("html" in kwargs)
			maybe_body   = ("body" in kwargs)
			maybe_xml    = ("xml" in kwargs)
		else:
			maybe_fields = is_iterable(args[0])

			if not maybe_fields and is_string(args[0]):
				maybe_url    = args[0].startswith(("http://", "https://", "ftp://", "file://"))
			else:
				maybe_url = False

			if not maybe_url and not maybe_fields:
				markup_type = self._guess_markup_type(args[0])
				maybe_html = markup_type == "html"
				maybe_xml  = markup_type == "xml"
				maybe_body = markup_type == "body"
			else:
				maybe_html = False
				maybe_xml  = False
				maybe_body = False
#			maybe_xml = is_valid_xml(args[0])

		if sum(1 for v in (maybe_fields, maybe_url, maybe_html, maybe_xml, maybe_body) if v) != 1:
			raise TypeError("Cannot interpret arguments to create_hit(..).  Please call with keyword arguments.")

		if maybe_url or maybe_html or maybe_body:
			if "height" not in kwargs and (len(args) < 2 or not isinstance(args[1], int)):
				raise TypeError("You must specify a height.")

		if maybe_url:
			return self._create_hit_from_url(*args, **kwargs)
		elif maybe_fields:
			return self._create_hit_from_fields(*args, **kwargs)
		elif maybe_xml:
			return self._create_hit_from_xml(*args, **kwargs)
		elif maybe_html:
			return self._create_hit_from_html(*args, **kwargs)
		elif maybe_body:
			return self._create_hit_from_body(*args, **kwargs)
		assert False

	def _guess_markup_type(self, markup):
		if not markup:
			raise ValueError("markup cannot be %r"%markup)
		if not is_string(markup):
			raise ValueError("markup must be a string, got a %r"%type(markup).__name__)

		markup_type = "unknown"

		if "QuestionForm" in markup:
			dom = xml2dom(markup, default=None)
			if dom is not None:
				if dom.documentElement.tagName == "QuestionForm":
					markup_type = "xml"
				elif dom.documentElement.tagName.lower() == "html":
					markup_type = "html"
				else:
					markup_type = "body"
				dom.unlink() # free up memory

		if markup_type is None:
			if markup[0].isspace():
				markup = markup.lstrip()

			if markup.startswith(("<html", "<!DOCTYPE", "<HTML")): # easy case
				markup = "html"
			else:
				if re.match(r'(?:<!--.*-->|\s+|<!doctype.*>)*<\s*html', markup, re.IGNORECASE | re.DOTALL) is not None:
					markup_type = "html"
				else:
					markup_type = "body"

		if markup_type is None:
			raise ValueError("Cannot determine type of markup passed to create_hit(..).  Please call with keyword arguments.")

		assert markup_type in ("xml", "html", "body")

		return markup_type



	def _create_hit_from_url(self, url, height, lifetime=None, max_assignments=None, requester_annotation=None):
		hit = self._amt.create_hit_from_url(
							url=url,
							frame_height=height,
							hit_type=self,
							lifetime=lifetime,
							max_assignments=max_assignments,
							requester_annotation=requester_annotation)
		return hit

	def _create_hit_from_body(self, body, height, onload="", style="", max_assignments=None, lifetime=None, requester_annotation=None):
		hit = self._amt.create_hit_from_html_parts(
							body=body,
							onload=onload,
							style=style,
							frame_height=height,
							hit_type=self,
							lifetime=lifetime,
							max_assignments=max_assignments,
							requester_annotation=requester_annotation)
		return hit

	def _create_hit_from_html(self, html, height, max_assignments=None, lifetime=None, requester_annotation=None):
		hit = self._amt.create_hit_from_html(
							html=html,
							frame_height=height,
							hit_type=self,
							lifetime=lifetime,
							max_assignments=max_assignments,
							requester_annotation=requester_annotation)
		return hit

	def _create_hit_from_xml(self, question_xml, max_assignments=None, lifetime=None, requester_annotation=None):
		try:
			hit = self._amt.create_hit(
						hit_type=self,
						question_xml=question_xml,
						max_assignments=max_assignments,
						lifetime=lifetime,
						requester_annotation=requester_annotation)
		except AMTRequestFailed:
			e = sys.exc_info()[1]
			if e.code=="AWS.MechanicalTurk.XMLParseError":
				raise QuestionXMLError(question_xml, e.code, e.msg)
		return hit

	def _create_hit_from_fields(self, fields, lifetime=None, max_assignments=None, requester_annotation=None):
		if not is_iterable(fields):
			fields = (fields,)
		hit = self._amt.create_hit_from_fields(
							fields=fields,
							hit_type=self,
							lifetime=lifetime,
							max_assignments=max_assignments,
							requester_annotation=requester_annotation)
		return hit

	def __repr__(self):
		return self.__class__.__name__ + repr(( self.id,
												self.title,
												self.description,
												self.reward,
												self.currency,
												self.time_limit,
												self.autopay_delay,
												self.keywords,
												self.qualification_requirements ))
	
	@property
	def average_time_taken(self):
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
			return to_duration(total_secs / float(total_non_rejected_assignments))
	
	@property
	def hourly_rate(self):
		# Excludes rejected work but includes work not yet approved/rejected.
		total_secs = 0.0
		total_non_rejected_assignments = 0
		for asg in self.assignments:
			if not asg.is_rejected:
				total_secs += float(total_seconds(asg.time_spent)) # float(..) probably unnecessary... paranoid.
				total_non_rejected_assignments += 1
		if total_secs==0:
			return None
		else:
			return (self.reward * total_non_rejected_assignments) / (total_secs / 60.0 / 60.0)
	
	def poll(self, duration="1 hour", interval="5 seconds"):
		# handler is a function that takes one parameter.

		# If callback_fn is None, then we will print a generic status message.

		class State(object): pass
		state = State()
		state.num_assignments_pending_all_hit_types = None

		class NoMoreAssignmentsException(Exception): pass

		def callback_fn():
			# [pylint] attributes of State being defined outside of State.__init__(..) : pylint:disable=W0201
			line = ""

			# We want something like this:
			#     12:58:30 PM:  789 of 758 asgs (0.0%) by 123 workers -- avg 36 secs/asg, $12.99/hr
			#     ________________________________________________________________________________ (80 chars)
			# Add time
			line += now_local().strftime("%I:%M:%S %p")
			line += ":  "

			# Add completion
			num_assignments_pending_all_hit_types = crowdlib.requester_statistics.number_assignments_pending
			if num_assignments_pending_all_hit_types != state.num_assignments_pending_all_hit_types:
			# If there are any new assignments...
				self._amt.sync_with_amt_to_update_assignment_counts()
				state.num_assignments_pending_all_hit_types = num_assignments_pending_all_hit_types
				state.assignments = tuple(self.assignments)
				state.num_done = len(state.assignments)
				state.num_desired = sum(hit.max_assignments for hit in self.hits)
				state.num_workers = len(set(asg.worker for asg in state.assignments))
				state.hourly_rate = self.hourly_rate
				state.avg_time = self.average_time_taken

			line += "%d of %d asgs"%(state.num_done, state.num_desired)
			line += " "
			if state.num_desired > 0:
				pct_done = float(state.num_done)/float(state.num_desired)
				if pct_done < 0.1:
					line += "(%.1f%%)"%(pct_done*100)
				else:
					line += "(%d%%)"%int(pct_done*100)
			line += " "
			line += "by %d workers"%state.num_workers

			# Add hourly rate, if applicable
			if state.hourly_rate is not None:
				line += ", "
				line += "avg %s/asg, $%.2f/hr"%(_format_duration(state.avg_time), state.hourly_rate)

			crowdlib.utility.clear_line()
			crowdlib.utility.dmp(line)

			if pct_done == 1.0:
				raise NoMoreAssignmentsException()

		try:
			crowdlib.utility.poll(duration=duration, interval=interval, callback_fn=callback_fn)
		except NoMoreAssignmentsException:
			crowdlib.utility.dmp("\n")

def _format_duration(dt, abbreviations=True):
	if isinstance(dt, (float, int)):
		secs = dt
	else:
		dt = to_duration(dt)
		secs = total_seconds(dt)
	if secs < 60:
		unit = ("sec" if abbreviations else "second")
		maybe_s = ("s" if secs != 1 else "")
		amt = int(round(secs))
		formatted_duration = "%d %s%s"%(amt, unit, maybe_s)
	else:
		if secs < 60*60:
			unit = ("min" if abbreviations else "minute")
			amt = secs / (60.0)
		elif secs < 60*60*24:
			unit = ("hr" if abbreviations else "hour")
			amt = secs / (60.0 * 60.0)
		else:
			unit = "day"
			amt = secs / (60.0 * 60.0 * 24.0)
		maybe_s = ("s" if round(amt)!=1.0 else "")
		amt = round(amt, 1)
		formatted_duration = "%.1f %s%s"%(amt, unit, maybe_s)
	return formatted_duration

if __name__=="__main__":
	sys.stderr.write( "\nThis is just a module, not the code entry point.\n" )
