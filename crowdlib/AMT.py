# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: January 2010
'''

# NOTE: The AMT class will call its own close() method when Python exists, using the `atexit` standard Python module.

from __future__ import division, with_statement

# [pylint] Tolerate too many public methods, branches, and instance attributes. : pylint:disable=R0904,R0912,R0902

from crowdlib.all_exceptions import AMTDataError, AMTNotificationNotAvailable, \
		AMTQualificationTypeAlreadyExists, AMTRequestFailed, AssignmentNotFoundException, \
		CrowdLibInternalError, CrowdLibSettingsError, HITNotFoundException, \
		HITTypeNotFoundException, QualificationTypeNotFoundException, WorkerNotFoundException
from crowdlib.AMTDB import AMTDB, DATABASE_ERROR_BASE_CLASS
from crowdlib.AMTMemoryCache import AMTMemoryCache
from crowdlib.AMTServer import AMTServer
from crowdlib.Answer import AnswerBlank, AnswerFreeText, AnswerSelection, AnswerUploadedFile
from crowdlib.Assignment import Assignment
from crowdlib.Bonus import Bonus
from crowdlib.currency_codes_iso_4217 import currency_codes_iso_4217
from crowdlib.HIT import HIT
from crowdlib.HITType import HITType
from crowdlib.NotificationEvent import NotificationEvent
from crowdlib.QualificationRequirement import QualificationRequirement
from crowdlib.QualificationType import QualificationType
from crowdlib.utility import dom_cdata, dom_element, duration_to_seconds, is_iterable, \
		is_sequence_of_strings, is_number, is_sequence, is_string, is_valid_xml, \
		make_xml_document_root_element_fn_cdatas_fn, to_date_time, \
		to_duration, to_unicode, urlopen_py23_compatible, urlretrieve_py23_compatible, \
		to_tuple_if_non_sequence_iterable
from crowdlib.utility.time_utils import now_local
from crowdlib.utility.debugging import dbg_log
from crowdlib.Worker import Worker
from xml.sax.saxutils import quoteattr
import atexit, cgi, datetime, functools, os, re, sys, textwrap, xml.dom.minidom as xdm

class AMT( object ):

	def __init__(self, settings):

		if not hasattr(self, "_already_initialized"):
			self._hit_sync_last_time = None
			self._hit_sync_interval = datetime.timedelta(seconds=60)
			# WARNING:  If _hit_sync_interval is too small, it will cause infinite loops.

			self._service_type                       = settings.service_type
			self._db_dir                             = settings.db_dir
			self._aws_account_id                     = settings.aws_account_id
			self._aws_account_key                    = settings.aws_account_key
			self._default_reward                     = settings.default_reward
			self._default_autopay_delay              = settings.default_autopay_delay
			self._default_currency                   = settings.default_currency
			self._default_lifetime                   = settings.default_lifetime
			self._default_max_assignments            = settings.default_max_assignments
			self._default_time_limit                 = settings.default_time_limit
			self._default_qualification_requirements = settings.default_qualification_requirements
			self._default_keywords                   = settings.default_keywords

			self._html_template = self._get_html_template()

			self._check_settings()

			self._server = AMTServer(self._aws_account_id, self._aws_account_key, self._service_type)

			self._memory_cache = AMTMemoryCache()

			self._db = self._set_up_db()

			if not self._db.is_new:
				self.sync_with_amt() # DB file was just created, so we must sync with the server.

			atexit.register(AMT.close, self)

			self._already_initialized = True
	
	def _get_html_template(self):
		# helper for __init__(..)
		crowdlib_src_dir = os.path.dirname(os.path.abspath(__file__))
		html_template_path = os.path.join(crowdlib_src_dir, "html_hit_template.html")
		with open(html_template_path, "rb") as infile:
			return infile.read().decode("utf8")
	
	def _check_settings(self):
		if not self._aws_account_id and not self._aws_account_key:
			raise CrowdLibSettingsError("No AWS account credentials.  Create a crowdlib_settings.py file with this and other information, and import it before doing any operations with CrowdLib."%self._aws_account_id)

		if self._aws_account_id=="":
			raise CrowdLibSettingsError("AWS Account ID in crowdlib_settings must not be %r."%self._aws_account_id)
		if self._aws_account_key=="":
			raise CrowdLibSettingsError("AWS Account Key ID in crowdlib_settings must not be %r."%self._aws_account_key)
		# helper for __init__(..)
		if self._db_dir is None:
			raise CrowdLibSettingsError("db_dir must be a directory path.  db_dir==%s"%repr(self._db_dir))
		if self._service_type not in ("sandbox", "production"):
			raise CrowdLibSettingsError("service_type must be \"sandbox\" or \"production\".  Got %s"%self._service_type)

	def _set_up_db(self):
		# helper for __init__(..)
		db_filename = ".".join(("crowdlib", self._aws_account_id, self._service_type, "sqlite3"))
		db_dir = os.path.abspath(self._db_dir)
		if not os.path.isdir(db_dir):
			os.makedirs(db_dir)
		db_path = os.path.join(db_dir, db_filename)

		#return AMTDB(db_path)
		return AMTDB(db_path, always_commit=True)  # FIXME: Why did you think this was needed?

	def open(self):
		self._db.open()

	def close(self):
		self._db.close()

	def do_request( self, operation, specific_parameters):
		return self._server.do_request(operation, specific_parameters)
	
	def create_hit_type(self, title, description=None, reward=None, currency=None, time_limit=None,
			                   keywords=None, autopay_delay=None, qualification_requirements=None):

		# Fill in defaults for any parameters that are None
		if reward is None:
			reward = self._default_reward
		if description is None:
			description = ""
		if currency is None:
			currency = self._default_currency
		if time_limit is None:
			time_limit = self._default_time_limit
		if keywords is None:
			keywords = self._default_keywords
		if autopay_delay is None:
			autopay_delay = self._default_autopay_delay
		if qualification_requirements is None:
			qualification_requirements = self._default_qualification_requirements

		# Convert duration parameters to a uniform type.
		time_limit = to_duration(time_limit)
		autopay_delay = to_duration(autopay_delay)

		assert currency in currency_codes_iso_4217
		assert is_number(reward)
		assert is_string(title)
		assert is_string(description)
		assert is_iterable(keywords)
		assert is_iterable(qualification_requirements)
		assert isinstance(autopay_delay, datetime.timedelta)
		assert isinstance(time_limit, datetime.timedelta)

		keywords = to_tuple_if_non_sequence_iterable(keywords)
		assert is_sequence_of_strings(keywords)

		qualification_requirements = tuple(qualification_requirements)
		assert all(isinstance(qr, QualificationRequirement) for qr in qualification_requirements)

		hit_type_id = self._server.register_hit_type( title=title, description=description,
				reward=reward, currency=currency, time_limit=time_limit,
				keywords=keywords,
				autopay_delay=autopay_delay, qualification_requirements=qualification_requirements)

		if self._memory_cache.has_hit_type(hit_type_id):
			hit_type = self._memory_cache.get_hit_type(hit_type_id)
		else:
			# Create the HITType object, which will be put into the database.
			hit_type = HITType(
				id                         = hit_type_id,
				title                      = title,
				description                = description,
				reward                     = reward,
				currency                   = currency,
				time_limit                 = time_limit,
				autopay_delay              = autopay_delay,
				keywords                   = keywords,
				qualification_requirements = qualification_requirements,
				amt                        = self
			)

			# Store in the database.
			self._db.put_hit_type(hit_type)

			# Store in the memory cache.
			self._memory_cache.put_hit_type(hit_type)

		assert isinstance(hit_type, HITType)
		return hit_type

	def url_for_hit_type_id(self,hit_type_id):
		return self._server.preview_hit_type_url_stem + hit_type_id

	def create_hit(self, hit_type, question_xml, max_assignments=None, lifetime=None, requester_annotation=None):

		unique_request_token = None # TODO: Implement this for real; not fully implemented as of 12/1/2013

		# Fill in defaults for any parameters that are None
		if lifetime is None:
			lifetime = self._default_lifetime
		if max_assignments is None:
			max_assignments = self._default_max_assignments
		if requester_annotation is None:
			requester_annotation = ""

		# Convert duration parameters to a uniform type.
		lifetime = to_duration(lifetime)

		hit_record = self._server.create_hit(
			hit_type_id          = hit_type.id,
			question_xml         = question_xml,
			lifetime_in_seconds  = duration_to_seconds(lifetime),
			max_assignments      = max_assignments,
			requester_annotation = requester_annotation,
			unique_request_token = unique_request_token
		)

		assert hit_record.num_pending==0
		assert hit_record.num_available==max_assignments
		assert hit_record.num_completed==0
		assert hit_record.hit_status==HIT.HIT_STATUS_ASSIGNABLE
		assert hit_record.requester_annotation==requester_annotation

		hit = HIT(
			id                   = hit_record.hit_id,
			hit_type             = hit_type,
			requester_annotation = hit_record.requester_annotation,
			max_assignments      = hit_record.max_assignments,
			question_xml         = question_xml,
			creation_time        = hit_record.creation_time,
			hit_status           = hit_record.hit_status,
			expiration_time      = hit_record.expiration_time,
			num_pending          = hit_record.num_pending,
			num_available        = hit_record.num_available,
			num_completed        = hit_record.num_completed,
			hit_review_status    = HIT.HIT_REVIEW_STATUS_NOT_REVIEWED,
			approximate_expiration_time    = None,
			amt                  = self
		)

		# Store in the database.
		self._db.put_hit(hit)

		hit_in_memory_cache = self._memory_cache.has_hit(hit_record.hit_id)
		assert not hit_in_memory_cache, "Already have HIT with ID %s.  Why??? (error #3162)"%hit_record.hit_id
		# This assertion was removed 8-18-2011 because it appears that I was
		# getting HIT IDs that had been seen before.  That might lead to
		# consistency bugs.  Need to investigate.  I re-enabled it on
		# 12/1/2013.  Although I never resolved the issue, enough has changed
		# in the last 2+ years that there's at least some chance that the bug
		# no longer exists.  We'll see. (ref#3125)

		# Store in the memory cache.
		self._memory_cache.put_hit(hit)
		# This also had been disabled at some point.  On 12-1-2013, I put it back. (ref#3126)

		return hit

	def create_hit_from_fields(self, fields, hit_type, lifetime, max_assignments, requester_annotation):
		from crowdlib.QuestionField import AbstractQuestionField, make_text_or_formatted_content_xml
#		from crowdlib.utility.xml_helpers import looks_like_limited_xhtml

		# Construct the XML dynamically using the xml.dom.minidom module.
		namespace = 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionForm.xsd'
		contents = []
		for field in fields:
			if isinstance(field, AbstractQuestionField):
				contents.append(field.xml)
#			elif looks_like_limited_xhtml(field):
#				contents.append("FormattedContent", *cdatas(field))
			elif is_string(field):
#				contents.append("Text", field)
				contents.append(make_text_or_formatted_content_xml(field))
			else:
				raise ValueError("Invalid field:  %r"%field)
		contents = "".join(contents)
		question_xml = "<QuestionForm xmlns=%(namespace)s>%(contents)s</QuestionForm>"%{
				"namespace" : quoteattr(namespace),
				"contents"  : "".join(contents)
		}
		# Create the HIT.
		hit = self.create_hit(
			hit_type             = hit_type,
			question_xml         = question_xml,
			max_assignments      = max_assignments,
			lifetime             = lifetime,
			requester_annotation = requester_annotation
		)
		return hit

	def _create_hit_from_url_or_html(self, which, content, frame_height, hit_type, lifetime, max_assignments, requester_annotation):
		if which == "url":
			root_node_name = "ExternalQuestion"
			namespace = 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd'
			url = content
		elif which == "html":
			root_node_name = "HTMLQuestion"
			namespace = "http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd"
			html = content
		else:
			assert False, "Unexpected value of `which`: %r"%which

		root,element,cdatas = make_xml_document_root_element_fn_cdatas_fn(root_node_name=root_node_name, namespace=namespace)

		if which == "url":
			root.appendChild(element("ExternalURL", url ))
		else:
			root.appendChild(element("HTMLContent", *cdatas(html) ))
		root.appendChild(element("FrameHeight", frame_height))
		question_xml = root.toxml()

		# Create the HIT.
		hit = self.create_hit(
			hit_type             = hit_type,
			question_xml         = question_xml,
			max_assignments      = max_assignments,
			lifetime             = lifetime,
			requester_annotation = requester_annotation
		)
		return hit

	def create_hit_from_html_parts(self, body, onload="", style="", *args, **kwargs):
		html = self._html_template%{"body":body, "onload":onload, "style":style}
		return self.create_hit_from_html(html=html, *args, **kwargs)

	def create_hit_from_html(self, html, *args, **kwargs):
		return self._create_hit_from_url_or_html(which="html", content=html, *args, **kwargs)

	def create_hit_from_url(self, url, *args, **kwargs):
		return self._create_hit_from_url_or_html(which="url", content=url, *args, **kwargs)

	def create_qualification_type( self, name, description, initially_active, keywords, retry_delay, test_xml,
			        answer_key_xml, test_duration, auto_granted, auto_granted_value):

		assert is_iterable(keywords)
		keywords = to_tuple_if_non_sequence_iterable(keywords)

		assert is_string(name)
		assert is_string(description)
		assert isinstance(initially_active, bool)
		assert is_sequence_of_strings(keywords)
		assert isinstance(retry_delay, datetime.timedelta), retry_delay
		assert (answer_key_xml is None) or (is_string(answer_key_xml) and is_valid_xml(answer_key_xml))
		assert isinstance(test_duration, datetime.timedelta)
		assert isinstance(auto_granted, bool)
		assert auto_granted_value is None or isinstance(auto_granted_value,int)

		kwargs = dict(
			name               = name,
			description        = description,
			initially_active   = initially_active,
			keywords           = keywords,
			retry_delay        = retry_delay,
			test_xml           = test_xml,
			answer_key_xml     = answer_key_xml,
			test_duration      = test_duration,
			auto_granted       = auto_granted,
			auto_granted_value = auto_granted_value,
		)
		try:
			qtype_id = self._server.create_qualification_type(**kwargs) # returns qualification_type_id
		except AMTQualificationTypeAlreadyExists:
			matches = self._search_qualification_types(name=name, description=description, test_xml=test_xml, keywords=keywords)
			if len(matches) == 1:
				qtype = matches[0]  # instance of QualificationType
			else:
				dbg_log("AMT says this QualificationType is duplicate.  When we searched AMT and the local DB by name, description, test XML, and keywords, we found %d matches"%len(matches)) #(ref#7055)
				raise
#			if len(matches)==0:
#				raise  # This would indicate a CrowdLib bug.  AMT says it already exists but we can't find it in server or DB???
#			elif len(matches) > 1:
#				raise AMTDataError("%d QualificationType matches by name, description, test XML, keywords"%len(matches)) #(ref#7055)
		else:
			qtype = QualificationType(id=qtype_id, creation_time=now_local(), **kwargs)
		return qtype

	def _search_qualification_types(self, name, description, test_xml, keywords):
		qtypes = self.get_qualification_types() # from both server and database
		matches = []
		for qt in qtypes:
			if (qt.name.strip() == name) \
					and (qt.description == description) \
					and (qt.test_xml is None or qt.test_xml == test_xml) \
					and (qt.keywords is None or sorted(qt.keywords)==sorted(keywords)):
				matches.append(qt)
		return tuple(matches)

	def create_click_through_qualification_requirement( self, name, description, xhtml, agree_text,
			   initially_active=True, keywords=None, required_to_preview=False): #remove_old=False, 

		# Primarily used for IRB informed consent form.  The given XHTML is displayed with a checkbox below it.

# TODO:  Add back in the ability to remove an old qualification type if need be.
#		if remove_old:
#			existing_qualification_types = self.get_my_qualification_types()
#			for id,nm in existing_qualification_types:
#				if nm==name:
#					self.dispose_qualification_type( id )

		qtype = self.create_qualification_type(
				name=name,
				description=description,
				initially_active=initially_active,
				keywords=keywords,
				retry_delay=datetime.timedelta(seconds=0),  # DEFAULT VALUE
				test_xml=self._create_click_through_qualification_requirement_question_xml(xhtml=xhtml, agree_text=agree_text),
				answer_key_xml=self._CLICK_THROUGH_QUALIFICATION_REQUIREMENT_ANSWER_KEY_XML,
				test_duration=datetime.timedelta(seconds=60*60*24),  # DEFAULT VALUE : allow 24 hours to view form
				auto_granted=False,   # DEFAULT VALUE
				auto_granted_value=1) # DEFAULT VALUE
		qreq = QualificationRequirement(qtype.id, "=", 1, locale_value=None, required_to_preview=required_to_preview)
		return qreq

	def _create_click_through_qualification_requirement_question_xml(self, xhtml, agree_text):

		# WEIRD CODE:  To build the XML for the qualification requirement, we use DOM
		# and build it programmatically.  "qf" is the DOM document.  element creates
		# an element with the specified contents.
		dom_impl = xdm.getDOMImplementation()
		namespace = 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionForm.xsd'
		doc = dom_impl.createDocument(namespace, "QuestionForm", None)
		qf = doc.documentElement
		qf.setAttribute( "xmlns", namespace )
		element = functools.partial( dom_element, doc )
		cdata = functools.partial( dom_cdata, doc )

		qf.appendChild(
			element( "Question",
				element( "QuestionIdentifier", "do_you_agree" ),
				element( "IsRequired", "true" ),
				element( "QuestionContent",
					element( "FormattedContent", cdata( xhtml ) ) ),
				element( "AnswerSpecification",
					element( "SelectionAnswer",
						element( "MinSelectionCount", "1" ),
						element( "StyleSuggestion", "checkbox" ),
						element( "Selections",
							element( "Selection",
								element( "SelectionIdentifier", "agree" ),
								element( "Text", agree_text )
		)	)	)	)	)	)
		question_form_xml = doc.toxml( encoding="UTF-8" )
		return question_form_xml

	_CLICK_THROUGH_QUALIFICATION_REQUIREMENT_ANSWER_KEY_XML = '''\
		<AnswerKey xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/AnswerKey.xsd">
		  <Question>
			<QuestionIdentifier>do_you_agree</QuestionIdentifier>
			<AnswerOption>
			  <SelectionIdentifier>agree</SelectionIdentifier>
			  <AnswerScore>1</AnswerScore>
			</AnswerOption>
		  </Question>
		</AnswerKey>'''

	def get_qualification_type(self, qualification_type_id):
		qualification_types = tuple(self.get_qualification_types())
		qualification_type = tuple(qt for qt in qualification_types if qt.id==qualification_type_id)
		if len(qualification_type)==1:
			return qualification_type[0]
		elif len(qualification_type)==0:
			raise QualificationTypeNotFoundException(qualification_type_id)
		else:
			raise AMTDataError("Didn't expect to find %d qualification types for the same ID."%(len(qualification_type)))

	def get_qualification_types(self):
		return self._server.get_qualification_types()

	def get_hit(self, hit_id, hit_type=None, hit_record=None):
		assert is_string(hit_id), hit_id

		hit = None

		# 1. Try the cache.
		try:
			hit = self._memory_cache.get_hit(hit_id)
		except HITNotFoundException:

			# 2. Try the DB
			try:
				hit_record = hit_record or self._db.get_hit_record(hit_id=hit_id)
				# (11/19/2013) Modified to allow passing in hit_record (for efficiency); might not be used at all

				if hit_type is None:
					# This hit_record does NOT have enough information to create the HITType.
					hit_type = self.get_hit_type(hit_type_id=hit_record.hit_type_id, hit_id=hit_id, do_sync_if_not_found=False)
					# This must have do_sync_if_not_found=False

				should_update_db = False

			except HITNotFoundException:

				# 3. Try the AMT server.
				hit_record = self._server.get_hit(hit_id=hit_id)

				if hit_type is None:
					# This hit_record DOES have enough information to create the HITType.
					hit_type = self.get_hit_type(hit_type_id=hit_record.hit_type_id, hit_record=hit_record, do_sync_if_not_found=False)
					# Not sure if this must have do_sync_if_not_found=False or not but that's how I found it.

				should_update_db = True

			assert isinstance(hit_type, HITType)

			hit = self._make_hit_from_hit_record(hit_record, hit_type)
			self._memory_cache.put_hit(hit)
			if should_update_db:
				self._db.put_hit(hit)

		assert hit.id == hit_id
		assert isinstance(hit, HIT)

		return hit

	def _make_hit_type_from_hit_record(self, hit_record):
		qrrs = hit_record.qualification_requirements
		qreqs = tuple(self._make_qualification_requirement_from_qualification_requirement_record(qrr) for qrr in qrrs)

		hit_type = HITType( id=hit_record.hit_type_id,
							title=hit_record.title,
							description=hit_record.description,
							reward=hit_record.reward.amount,
							currency=hit_record.reward.currency_code,
							time_limit=hit_record.assignment_duration,
							autopay_delay=hit_record.auto_approval_delay,
							keywords=hit_record.keywords,
							qualification_requirements=qreqs,
							amt=self)
		return hit_type
	
	def _make_hit_from_hit_record(self, hit_record, hit_type):
		approximate_expiration_time = getattr(hit_record, "approximate_expiration_time", None)
		hit = HIT( id=hit_record.hit_id,
				   hit_type = hit_type,
				   question_xml = hit_record.question,
				   max_assignments = hit_record.max_assignments,
				   requester_annotation = hit_record.requester_annotation,
				   creation_time = hit_record.creation_time,
				   hit_status = hit_record.hit_status,
				   expiration_time = hit_record.expiration_time,
				   num_pending   = hit_record.num_pending,
				   num_available = hit_record.num_available,
				   num_completed = hit_record.num_completed,
				   hit_review_status = hit_record.hit_review_status,
				   approximate_expiration_time = approximate_expiration_time,
				   amt=self)
		return hit

	def _make_qualification_requirement_from_qualification_requirement_record(self, qualification_requirement_record):
		qreq = QualificationRequirement(
				qualification_type_id=qualification_requirement_record.qualification_type_id,
				comparator=qualification_requirement_record.comparator,
				integer_value=qualification_requirement_record.integer_value,
				locale_value=qualification_requirement_record.locale_value,
				required_to_preview=qualification_requirement_record.required_to_preview)
		return qreq

	def suggest_hit_sync(self, hit_type_id=None, must_sync=False):
		# hit_type_id is only used to see if the given HITType has notifications working.  If
		# so, then we do nothing.

		SKIP_SYNC_IF_NOTIFICATIONS_ARE_ACTIVE_AND_WORKING = False # This isn't working, yet.

		now = now_local()
		just_connected = False
		if hit_type_id:
			hit_sync_last_time = self._hit_sync_last_time

			# NEW APPROACH (not working, yet):  If notifications have been enabled and the first
			# notification has been received, then don't bother syncing.

			if SKIP_SYNC_IF_NOTIFICATIONS_ARE_ACTIVE_AND_WORKING:
				if hit_sync_last_time:
					try:
						notification_hit_type_registration = self._db.get_notification_hit_type_registration(hit_type_id=hit_type_id)
					except HITTypeNotFoundException:
						pass
					else:
						max_notification_activation_delay = datetime.timedelta(minutes=5)
						is_connected = notification_hit_type_registration.is_connected
						registered_time = notification_hit_type_registration.registered_time
						was_test_received = notification_hit_type_registration.test_received_time is not None
						last_received_time = notification_hit_type_registration.last_received_time

						if is_connected:
							return False
						elif was_test_received and hit_sync_last_time - registered_time >= max_notification_activation_delay:
							self._db.set_notification_hit_type_is_connected(hit_type_id)
							return False
						elif last_received_time is not None:
							assert was_test_received, (hit_type_id, notification_hit_type_registration)
							just_connected = True

		if (self._hit_sync_last_time is None) or (now - self._hit_sync_last_time > self._hit_sync_interval) or must_sync: 
			self._hit_sync_last_time = now
			self.sync_with_amt()
			if SKIP_SYNC_IF_NOTIFICATIONS_ARE_ACTIVE_AND_WORKING:
				if just_connected:
					self._db.set_notification_hit_type_is_connected(hit_type_id)
			return True
		else:
			return False

	def sync_with_amt(self):
		hit_ids_seen = []
		hit_records_from_db = dict((hr.hit_id, hr) for hr in self._db.get_hit_records())

		for hit_record in self._server.search_hits():
			hit_record_from_db = hit_records_from_db.get(hit_record.hit_id, None)
			hit_ids_seen.append( hit_record.hit_id)  # >=20131120

			# The hit_record returned by SearchHITs does not contain the qualification_requirements
			# so instead of passing the hit_record to get_hit_type, we will pass only the hit_id.
			# That will typically cause get_hit_type to fetch the details using GetHIT, which should
			# return the needed info.
			hit_type = self.get_hit_type(hit_type_id=hit_record.hit_type_id, hit_id=hit_record.hit_id, do_sync_if_not_found=False)
			try:
				hit = self.get_hit(hit_id=hit_record.hit_id, hit_type=hit_type, hit_record=hit_record_from_db)
				# [pylint] Tolerate access of protected member _update_from_amt. : pylint:disable=W0212
				should_update = hit._update_from_amt(
					 expiration_time=hit_record.expiration_time,
					 max_assignments=hit_record.max_assignments,
					 num_pending=hit_record.num_pending,
					 num_completed=hit_record.num_completed,
					 num_available=hit_record.num_available,
					 hit_status=hit_record.hit_status,
					 question_xml=hit_record.question,
					 approximate_expiration_time=None,  # be explicit, we are setting this to NULL because we now have the real value
					 )
			except HITNotFoundException:
				hit = self._make_hit_from_hit_record(hit_record=hit_record, hit_type=hit_type)
				self._memory_cache.put_hit(hit)
				should_update = True

			if should_update: # added this check on 11-13-2013
				self._db.put_hit(hit)

		known_hit_ids_not_disposed = self._db.get_known_hit_ids_except_hit_status(HIT.HIT_STATUS_DISPOSED)
		hit_ids_recently_disposed = set(known_hit_ids_not_disposed) - set(hit_ids_seen)
		self._db.set_hit_statuses(hit_ids_recently_disposed, HIT.HIT_STATUS_DISPOSED)

	sync_with_amt_to_update_assignment_counts = sync_with_amt # just an alias to make other code clearer

	def get_requester_statistic(self, statistic, time_period):
		# The max count is 730.  Discovered by experiment on 2-14-2011.
		if time_period=="OneDay":
			count = 730  # Get as many as possible.  This seems to be the max, based on experiment 2-14-2011.
			stats = self._server.get_requester_statistic(statistic=statistic, time_period=time_period, count=count)
			return stats
		else:
			stats = self._server.get_requester_statistic(statistic=statistic, time_period=time_period)
			single_stat = stats[0][1]
			return single_stat

	def get_worker(self, worker_id):
		assert is_string(worker_id), worker_id
		try:
			return self._memory_cache.get_worker(worker_id)
		except WorkerNotFoundException:
			worker = Worker(worker_id, self)
			self._memory_cache.put_worker(worker)
			return worker

	def get_hits(self, since=None, until=None, title_re=None):
		for hit_type in self.get_hit_types():
			for hit in hit_type.hits:
				if self._hit_matches_criteria(hit, since, until, title_re):
					yield hit
	
	def set_all_hits_unavailable(self):
		for hit in self.get_hits():
			try:
				hit.is_available = False
			except AMTRequestFailed:
				pass

	def _hit_matches_criteria(self, hit, since, until, title_re):
		# Any of these criteria may be None, indicating that it should not be applied.
		if (since is None) and (until is None) and (title_re is None):
			return True
		elif (since is not None) and not (hit.expiration_time > since):
			return False
		elif (until is not None) and not (hit.creation_time < until):
			return False
		elif (title_re is not None) and not (re.match(title_re, hit.hit_type.title)):
			return False
		else:
			return True

	def _hit_type_matches_criteria(self, hit_type, since, until, title_re):
		# Return True iff *any* hit in the hit_type matches the given criteria.
		# Any of the criteria may be None.  Return True if all are None.
		if title_re is not None and re.match(title_re, hit_type.title) is None:
			return False
		elif (since is None) and (until is None):
			return True
		else:
			assert title_re is None or re.match(title_re, hit_type.title)
			assert since is not None or until is not None
			return any(self._hit_matches_criteria(hit, since, until, title_re=None) for hit in hit_type.hits)

	def _assignment_matches_criteria(self, assignment, since, until, title_re):
		if (since is None) and (until is None) and (title_re is None):
			return True
		elif (since is not None) and not (assignment.submit_time > since):
			return False
		elif (until is not None) and not (assignment.accept_time < until):
			return False
		elif (title_re is not None) and not (re.match(title_re, assignment.hit.hit_type.title)):
			return False
		else:
			return True

	def get_hits_for_hit_type(self, hit_type, since=None, until=None, title_re=None):

		# Fetch all HITs for this HITType from the DB, but if a HIT was
		# already in the memory cache, then return that one.  We should never
		# have two copies of the same HIT in memory at once.

		for hit_record in self._db.get_hit_records(hit_type_id=hit_type.id):
			try:
				# If already in the DB, then use that.
				hit = self._memory_cache.get_hit(hit_record.hit_id)
			except HITNotFoundException:
				# Otherwise, use what we found in the DB.
				hit = self._make_hit_from_hit_record(hit_record=hit_record, hit_type=hit_type)
				self._memory_cache.put_hit(hit)
			if self._hit_matches_criteria(hit=hit, since=since, until=until, title_re=title_re):
				yield hit
	
	def get_hit_types(self, since=None, until=None, title_re=None):
		# Fetch all known HITTypes from the DB, but if a HITType was already
		# in the memory cache, then return that one.

		for hit_type_record in self._db.get_hit_type_records():
			hit_type_id = hit_type_record.hit_type_id
			hit_type = None
			if self._memory_cache.has_hit_type(hit_type_id):
				hit_type = self._memory_cache.get_hit_type(hit_type_id)
			else:
				hit_type = self._make_hit_type_from_hit_record(hit_type_record)
				self._memory_cache.put_hit_type(hit_type)
			
			if self._hit_type_matches_criteria(hit_type, since, until, title_re):
				yield hit_type
	
	def get_hit_type(self, hit_type_id, hit_id=None, hit_record=None, do_sync_if_not_found=False):
		hit_type = None

		assert not ((hit_id is not None) and (do_sync_if_not_found==True)), \
				"We will never do a sync if hit_id was provided, since the hit_id allows us to " \
				"request the information directly without going through unrelated HITs."

		assert (hit_record is None) or (hit_record.hit_type_id==hit_type_id)

		try:
			# 1. Try the memory cache.
			hit_type = self._memory_cache.get_hit_type(hit_type_id=hit_type_id)

		except HITTypeNotFoundException:
			#2. Try the hit_record, if passed in.
			if hit_record is not None:
				hit_type = self._make_hit_type_from_hit_record(hit_record=hit_record)
			else:
				try:
					# 3. Try the DB.
					hit_type_record = self._db.get_hit_type_record(hit_type_id)
					hit_type = self._make_hit_type_from_hit_record(hit_type_record)
					self._memory_cache.put_hit_type(hit_type)
					# On 7-4-2014, I got CrowdLibInternalError from the above call to put_hit_type(hit_type).

				except HITTypeNotFoundException:
					if hit_id is not None:
						# 4. Try fetching a hit_record, if we have the hit_id.
						hit_record = self._server.get_hit(hit_id=hit_id)
						hit_type = self._make_hit_type_from_hit_record(hit_record=hit_record)
						self._memory_cache.put_hit_type(hit_type)
						self._db.put_hit_type(hit_type)

					elif do_sync_if_not_found:
						# 5. Try doing a full sync.
						self.suggest_hit_sync()
						hit_type = self.get_hit_type(hit_type_id=hit_type_id,
													 hit_record=hit_record,
													 do_sync_if_not_found=False)  # RECURSIVE
					else:
						# 6. Give up.  :(
						raise

		assert isinstance(hit_type, HITType)
		assert hit_type.id==hit_type_id

		return hit_type

	def get_assignment(self, assignment_id, hit_id=None):
		# If this assignment ID has never been seen, you will get an error.

		if hit_id is None:
			hit_id = self._db.get_hit_id_for_assignment_id(assignment_id)
			# Will raise AssignmentNotFoundException if this assignment has never been
			# seen by this instance of CrowdLib.  May need to call sync_with_amt()

		hit = self.get_hit(hit_id=hit_id)
		# Might raise HITNotFoundException if the HIT is 

		try:
			assignment_record = self._db.get_assignment_record(assignment_id=assignment_id)
			worker = self.get_worker(assignment_record.worker_id)
			assignment = self._make_assignment(assignment_record=assignment_record, hit=hit, worker=worker)
		except AssignmentNotFoundException:
			assignments = tuple( asg for asg in self.get_assignments_for_hit(hit=hit) if asg.id==assignment_id)
			if len(assignments)==1:
				assignment = assignments[0]
			elif len(assignments)==0:
				raise
			else:
				assert False, repr(assignments)
		return assignment
	
	def _make_assignment(self, assignment_record, hit, worker=None):
		if worker is None:
			worker = self.get_worker(worker_id=assignment_record.worker_id)

		answer_records = assignment_record.answer_records
		assignment_id = assignment_record.assignment_id
		answers = tuple(self._make_answer(answer_record=answer_record, assignment_id=assignment_id) for answer_record in answer_records)

		asg = Assignment(
				id=assignment_record.assignment_id,
				worker=worker,
				hit=hit,
				assignment_status=assignment_record.assignment_status,
				autopay_time=assignment_record.auto_approval_time,
				accept_time=assignment_record.accept_time,
				submit_time=assignment_record.submit_time,
				approval_time=assignment_record.approval_time,
				rejection_time=assignment_record.rejection_time,
				requester_feedback=assignment_record.requester_feedback,
				answers=answers,
				amt=self)

		return asg
	
	def _make_answer(self, answer_record, assignment_id):
		if answer_record.selection_identifier is not None:
			answer = AnswerSelection(question_id=answer_record.question_identifier,
									 selection_id=answer_record.selection_identifier,
									 other_selection_text=answer_record.other_selection,
									 assignment_id=assignment_id,
									 amt=self)
		elif answer_record.uploaded_file_key is not None:
			answer = AnswerUploadedFile(question_id=answer_record.question_identifier,
										uploaded_file_key=answer_record.uploaded_file_key,
										uploaded_file_size=answer_record.uploaded_file_size,
										assignment_id=assignment_id,
										amt=self)
		elif answer_record.free_text is not None:
			answer = AnswerFreeText(question_id=answer_record.question_identifier,
									free_text=answer_record.free_text,
									assignment_id=assignment_id,
									amt=self)
		else:
			answer = AnswerBlank(assignment_id=assignment_id)
		return answer

	def get_reviewable_hits(self, hit_type):
		assert isinstance(hit_type, HITType)
		for hit_id in self._get_reviewable_hit_ids(hit_type=hit_type):
			assert hit_id is not None
			hit = self.get_hit(hit_id, hit_type)
			if hit.hit_status!=HIT.HIT_STATUS_REVIEWABLE:
				hit.sync_with_amt()
			yield hit

	def _get_reviewable_hit_ids(self, hit_type=None): # GENERATOR
		if hit_type is None:
			hit_type_id = None
		else:
			hit_type_id = hit_type.id
		return self._server.get_reviewable_hit_ids(hit_type_id=hit_type_id) # generator

	def extend_hit(self, hit, max_assignments_increment=0, expiration_increment=0):
		max_assignments_increment = int(round(max_assignments_increment,0))
		expiration_increment = int(round(expiration_increment,0))
		assert max_assignments_increment>=0 and expiration_increment>=0
		assert max_assignments_increment>0  or  expiration_increment>0
		self._server.extend_hit_id(hit_id=hit.id,
				                   max_assignments_increment=max_assignments_increment,
				                   expiration_increment=expiration_increment)
		changes = hit._update_from_amt_due_to_extend_hit( # [pylint] accessing friend method : pylint:disable=W0212
			max_assignments_increment=max_assignments_increment,
			expiration_increment=expiration_increment
		)
		if changes:
			self._db.update_hit(hit_id=hit.id, **changes)

	def unblock_worker_id( self, worker_id, reason ):
		# http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/ApiReference_BlockWorkerOperation.html
		# Turker will not see the reason.  Reason is NOT required for unblock
		self._server.unblock_worker_id(worker_id, reason)
		self._db.update_worker_unblocked(worker_id)

	def block_worker_id( self, worker_id, reason ):
		# Reason is required for block and thus may not be None or "".
		# http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/ApiReference_UnblockWorkerOperation.html
		self._server.do_request("BlockWorker", {"WorkerId" : worker_id, "Reason" : reason})
		self._db.update_worker_blocked(worker_id, reason)
	
	def is_worker_id_blocked(self, worker_id):
		return self._db.is_worker_id_blocked(worker_id)

	def get_worker_block_reason(self, worker_id):
		return self._db.get_worker_block_reason(worker_id)

	def notify_worker( self, worker_id, subject, message_text ):
		self.notify_workers((worker_id,), subject, message_text)

	def notify_workers( self, workers_or_worker_ids, subject, message_text ):
		worker_ids = tuple((w.id if isinstance(w,Worker) else w) for w in workers_or_worker_ids)
		send_time = now_local()
		email_wrap = 65
		message_text = "\n".join(textwrap.fill(s,email_wrap) for s in message_text.splitlines())
		for i in range(0,len(worker_ids),100):
			worker_id_batch = worker_ids[i:i+100]
			self._server.notify_workers(worker_ids=worker_ids, subject=subject, message_text=message_text)
			for worker_id in worker_id_batch:
				try:
					self._db.record_worker_message(worker_id=worker_id,
							                       send_time=send_time,
												   subject=subject,
												   message_text=message_text)
				except DATABASE_ERROR_BASE_CLASS:
					raise CrowdLibInternalError("Could not record sending of message to worker(s) in local DB. (error#2191)\n"
							+ repr(sys.exc_info()[1]))
	
	def get_workers(self, since=None, until=None, title_re=None):
		worker_ids_seen_so_far = set()
		for hit_type in self.get_hit_types():
			for hit in hit_type.hits:
				for assignment in hit.assignments:
					if self._assignment_matches_criteria(assignment=assignment, since=since, until=until, title_re=title_re):
						worker = assignment.worker
						worker_id = worker.id
						if worker_id not in worker_ids_seen_so_far:
							worker_ids_seen_so_far.add(worker_id)
							yield worker

	def get_assignments(self, since=None, until=None, title_re=None):
		for hit in self.get_hits(since=since, until=until, title_re=title_re):
			for asg in self.get_assignments_for_hit(hit):
				if self._assignment_matches_criteria(assignment=asg, since=since, until=until, title_re=title_re):
					yield asg

	def get_assignments_for_hit(self, hit):
		# This doesn't refetch assignments just because they're not finalized, yet.
		# At this stage, all we should care about is if we have all of them,
		# not the status.  That logic is handled by the Assignment class when
		# you call the relevant properties.


		# NOTE:  This function may be called as a result of aggregate HIT properties,
		# such as hourly_rate and average_time_taken.

		BE_LAZY = True  # Don't re-download assignments for any HIT.  The only reason to
		                # do that would be to see the status (i.e., approved, rejected, submitted)
						# and that can/should be done by Assignment, lazily.
		assignments_dict = {}
		max_assignments = hit.max_assignments

		if not BE_LAZY:
			expected_num_finalized = hit.num_completed

		def seems_up_to_date():
			if BE_LAZY:
				result = (len(assignments_dict) == (max_assignments - hit.num_available - hit.num_pending))
			else:
				# Helper:  Return true iff we already have all assignments for this HIT.
				# This can be determined by comparing the assignments seen so far with
				# the metrics in the HIT, such as num_pending, num_completed, and
				# num_available.

				# Number of assignments that are final (already approved or rejected)
				num_finalized = sum(1 for asg in assignments_dict.values() if asg.is_final)

				# Have we received and finalized (approved or rejected) all of the HITs we asked for?
				have_all = (num_finalized == max_assignments)

				# ??? What's this next statement for? ???
				all_appear_current = (num_finalized == expected_num_finalized)
				result = (have_all and all_appear_current)
			return result

		def handle_assignment_record(assignment_record, info_from_db):
			# If info came from DB, then probably don't need to write it back to the DB, unless
			# something changed.
			# ??? -- I don't believe anything would ever change.  You just read it out of the DB.
			# The Assignment constructor doesn't make any changes.  That code is probably unnecessary
			# if the code came from the DB.  The only aspects of an Assignment that could change
			# are approval_time, rejection_time, assignment_status, and requester_feedback.
			# TODO:  Probably remove the unnecessary code.  Too paranoid right now.
			write_to_db = not info_from_db

			assignment_id = assignment_record.assignment_id
			if assignment_id in assignments_dict:
				assignment = assignments_dict[assignment_id]
				# [pylint] Tolerate access to protected member _update_status_from_amt : pylint:disable=W0212
				changed = assignment._update_status_from_amt(
						assignment_status=assignment_record.assignment_status,
						approval_time=assignment_record.approval_time,
						rejection_time=assignment_record.rejection_time)
				assert isinstance(changed, bool)
				if changed:
					# Something changed.  Write changes back to DB.
					write_to_db = True
			else:
				assignment = self._make_assignment(assignment_record=assignment_record, hit=hit)
				assignments_dict[assignment.id] = assignment
				self._memory_cache.put_assignment(assignment)

			if write_to_db:
				self._db.put_assignment(assignment)
			return assignment

		# 1. Try the memory cache.
		for asg in self._memory_cache.get_assignments_for_hit_id(hit_id=hit.id):
			assignments_dict[asg.id] = asg

		# 2. Add in whatever we have in the DB, if needed.
		if not seems_up_to_date():
			for assignment_record in self._db.get_assignment_records(hit_id=hit.id):
				asg = handle_assignment_record(assignment_record=assignment_record, info_from_db=True)

			# 3. Try server.
			if not seems_up_to_date():
				for assignment_record in self._server.get_assignments_for_hit(hit=hit):
					asg = handle_assignment_record(assignment_record=assignment_record, info_from_db=False)

				if not seems_up_to_date():
					if BE_LAZY:
#						for asg in sorted(assignments_dict.values(), key=lambda asg:asg.id):
#							log( "assignment_id=%s   worker_id=%s   submitted=%s"%(asg.id,asg.worker.id,asg.submit_time) )
						raise AMTDataError(
							"Number of assignments returned from AMT doesn't match the predicted count in the HIT structure.  " \
							"len(assignments_dict)==%d,  max_assignments==%d,  hit.num_available==%s,  hit.num_pending==%d"% \
							(len(assignments_dict),      max_assignments,      hit.num_available,      hit.num_pending) )
					else:
						raise AMTDataError(
							"Number of assignments returned from AMT doesn't match the predicted count in the HIT structure." )

		assignments = assignments_dict.values()
		assignments = sorted(assignments, key=lambda asg:asg.submit_time)
		assignments = tuple(assignments)

		return assignments

	def force_expire_hit( self, hit ):
		self._server.force_expire_hit(hit_id=hit.id)
		approximate_expiration_time = now_local()
		changes = hit._set_force_expired_from_amt( # [pylint] accessing friend method : pylint:disable=W0212
				approximate_expiration_time=approximate_expiration_time)
		if changes:
			self._db.update_hit(hit_id=hit.id, **changes)

	def reject_assignment(self, assignment, reason, rejection_time):
		# reason may be None
		self._server.reject_assignment(assignment, reason)
		self._db.update_assignment_rejected(assignment.id, rejection_time)

	def approve_assignment(self, assignment, requester_feedback, approval_time):
		# requester_feedback may be None
		self._server.approve_assignment(assignment, requester_feedback)
		self._db.update_assignment_approved(assignment.id, approval_time)

	def reject_assignment_id(self, assignment_id, reason, rejection_time):
		# reason may be None
		self._server.reject_assignment(assignment_id, reason)
		self._db.update_assignment_rejected(assignment_id, rejection_time)

	def approve_assignment_id(self, assignment_id, requester_feedback, approval_time):
		# requester_feedback may be None
		self._server.approve_assignment(assignment_id, requester_feedback)
		self._db.update_assignment_approved(assignment_id, approval_time)

	def grant_bonus(self, assignment_id, worker_id, amount, currency, reason):
		# reason may be None
		if currency is None:
			currency = self._default_currency
		self._server.grant_bonus(assignment_id, worker_id, amount, currency, reason)
		payment_time = now_local()
		self._db.record_worker_bonus(worker_id, assignment_id, amount, currency, payment_time, reason)

	def get_bonuses(self, assignment_id=None, worker_id=None):
		for bonus_record in self._db.get_bonuses(assignment_id, worker_id):
			bonus = Bonus(
					assignment_id=bonus_record.assignment_id,
					worker_id=bonus_record.worker_id,
					amount=bonus_record.amount,
					currency=bonus_record.currency,
					payment_time=bonus_record.payment_time,
					reason=bonus_record.reason,
					amt=self
			)
			yield bonus

	def get_account_balance( self ):
		account_balance = self._server.get_account_balance()
		if account_balance.currency_code != self._default_currency:
			raise ValueError("Unexpected currency %s doesn't match %s"%(account_balance.currency_code, self._default_currency))
		return account_balance.amount

	def start_notifications(self, url):  # DO NOT USE - new feature in progress, not fully implemented
		active_hit_types = set()
		for hit in self.get_hits():
			if hit.hit_status != HIT.HIT_STATUS_DISPOSED and hit.num_pending + hit.num_available > 0:
				active_hit_types.add( hit.hit_type ) # TODO: Do as a batch operation, for efficiency.

		assert len(active_hit_types) == len(set(ht.id for ht in active_hit_types))
		for hit_type in active_hit_types:
			print( "Active HIT Type:  " + hit_type.id )
			self.set_hit_type_notification(hit_type_id=hit_type.id, address=url, transport="REST", event_type=AMTServer.NOTIFICATION_EVENT_TYPES_ALL)
#		self._db.set_notification_started(url)
#		self.send_test_notification(url)

	def stop_notifications(self):  # DO NOT USE - new feature in progress, not fully implemented
		for hit_type_id in self._db.get_notification_hit_type_ids_registered():
			self.set_hit_type_notification(hit_type_id=hit_type_id, address=None, transport=None, event_type=AMTServer.NOTIFICATION_EVENT_TYPES_ALL)
		self._db.set_notification_stopped()
	
	def _get_active_hit_type_ids(self):
		active_hit_type_ids = set()
		for hit in self.get_hits():
			if hit.hit_status != HIT.HIT_STATUS_DISPOSED and hit.num_pending + hit.num_available > 0:
				active_hit_type_ids.add(hit.hit_type.id)

	def get_current_notification_events_from_cgi(self, cgi_fields=None):
		if cgi_fields is None:
			cgi_fields = cgi.FieldStorage()
			cgi_fields = dict((k, cgi_fields.getfirst(k, None)) for k in cgi_fields.keys())
#		service = "AWSMechanicalTurkRequesterNotification"
#		operation = "Notify"
		method = cgi_fields.get("method", None)
		version = cgi_fields.get("Version", None)
		timestamp = cgi_fields.get("Timestamp", None)
		signature = cgi_fields.get("Signature", None)
		if (method is None) or (method != "Notify") or (version is None) or (timestamp is None) or (signature is None):
			raise AMTNotificationNotAvailable("Notification fields are not complete. (7010)")

		notification_events = []
		for i in range(1,1000):  # normally, this will quit after 1 or a few iterations.
			stem = "Event.%d."%i
			event_type    = cgi_fields.get(stem+"EventType",    None)
			event_time    = cgi_fields.get(stem+"EventTime",    None)
			hit_type_id   = cgi_fields.get(stem+"HITTypeId",    None)
			hit_id        = cgi_fields.get(stem+"HITId",        None)
			assignment_id = cgi_fields.get(stem+"AssignmentId", None)

			if (event_type is None) and (event_time is None) and (hit_type_id is None) and (hit_id is None):
				break
			elif (event_type is not None) and (event_time is not None):
				assert (hit_type_id is None) == (hit_id is None)
				event_time = to_date_time(event_time)
				event_type = to_unicode(event_type)
				if hit_type_id is not None:
					hit_type_id = to_unicode(hit_type_id)
					hit_id = to_unicode(hit_id)
					hit      = self.get_hit(hit_id)
					hit_type = hit.hit_type
					if assignment_id is not None:
						assignment_id = to_unicode(assignment_id)
						assignment= self.get_assignment(assignment_id, hit_id=hit_id)
					else:
						assignment= None
					notification_event = NotificationEvent(event_type, event_time, hit_type, hit, assignment)
					notification_events.append(notification_event)
					self._db.set_notification_hit_type_received(hit_type_id)
				else:
					self._db.set_notification_test_received()
				# If we get event_type and event_time but not hit_type_id and hit_id, it's probably a Ping or
				# some other test event.  Just ignore it.

				self.sync_with_amt()
			else:
				raise AMTNotificationNotAvailable("Notification fields are not complete. (7011)", (event_type, event_type, hit_type_id, hit_id, i))
		return notification_events

	def send_test_notification(self, address, event_type=None):  # event_type defaults to AMTServer.NOTIFICATION_EVENT_TYPE_SUBMITTED
		if event_type is None:
			event_type = AMTServer.NOTIFICATION_EVENT_TYPE_SUBMITTED
		assert event_type in AMTServer.NOTIFICATION_EVENT_TYPES_ALL
		transport = self._guess_notification_address_transport(address)
		self._server.send_test_event_notification(address=address, transport=transport, event_type=event_type)

	def set_hit_type_notification(self, hit_type_id, address, transport, event_type):
		assert (address is None)==(transport is None)
		if event_type is None:
			event_type = AMTServer.NOTIFICATION_EVENT_TYPE_SUBMITTED

		if event_type in AMTServer.NOTIFICATION_EVENT_TYPES_ALL:
			event_types = (event_type,)
		elif is_sequence(event_type):
			event_types = event_type

		assert is_sequence(event_types) and all(et in AMTServer.NOTIFICATION_EVENT_TYPES_ALL for et in event_types), event_types

		if address is None:
			self._server.set_hit_type_notification_inactive(hit_type_id)
#			self._db.put_hit_type_notification_url(hit_type_id=hit_type_id, url=None)
			self._db.set_notification_hit_type_unregistered(hit_type_id)
		else:
			transport = self._guess_notification_address_transport(address)
			self._server.set_hit_type_notification(hit_type_id=hit_type_id, address=address, transport=transport, event_types=event_type)
#			self._db.put_hit_type_notification_url(hit_type_id=hit_type_id, url=address)
			self._db.set_notification_hit_type_registered(hit_type_id)

	def _guess_notification_address_transport(self, address):
		# SOAP is not currently supported.
		if address.startswith("http://") or address.startswith("https://"):
			return "REST"
		elif address.count("@")==1 and address.count(".") >= 1:
			return "Email"
		else:
			raise ValueError("%s does not appear to be either a valid URL or Email address."%address)
	
	def save_file_answer_content(self, assignment_id, question_id, path):
		url = self._server.get_file_upload_url(assignment_id=assignment_id, question_id=question_id)
		urlretrieve_py23_compatible(url=url, filename=path)

	def get_file_answer_content(self, assignment_id, question_id):
		url = self._server.get_file_upload_url(assignment_id=assignment_id, question_id=question_id)
		infile = urlopen_py23_compatible(url=url)
		content = infile.read()
		infile.close()
		return content





#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# EXPERIEMENTAL CODE (do not delete, yet)
#

#	def get_hit_type_notification_url(self, hit_type_id):
#		url = self._db.get_hit_type_notification_url(hit_type_id)
#		return url

#	def set_hit_type_notification_url(self, hit_type_id, url):
#		# Per documentation:
#		# "After you make the call to SetHITTypeNotification, it can take up to five minutes for
#		# changes to a HIT type's notification specification to take effect."
#		# http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/ApiReference_SetHITTypeNotificationOperation.html
#		url = self._db.put_hit_type_notification_url(hit_type_id, url)
