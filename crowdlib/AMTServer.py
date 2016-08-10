# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: November 2010
'''
import datetime, sys
from crowdlib.all_exceptions import AMTRequestFailed, AssignmentAlreadyFinalizedException, XMLProcessingException
from crowdlib.AMTServerConnection import AMTServerConnection
from crowdlib.AnswerRecord import AnswerRecord
from crowdlib.AssignmentRecord import AssignmentRecord
from crowdlib.HITRecord import HITRecord
from crowdlib.QualificationRequirement import QualificationRequirement
from crowdlib.QualificationRequirementRecord import QualificationRequirementRecord
from crowdlib.QualificationType import QualificationType
from crowdlib.Reward import Reward
from crowdlib.utility import bool_in_element, datetime_in_element, duration_in_element, is_number, is_sequence_of, is_sequence_of_strings, is_string, number_in_element, parse_iso_utc_to_datetime_local, text_in_element, text_node_content, to_boolean, to_duration, to_tuple_if_non_sequence_iterable, to_unicode, total_seconds, xml2dom, xml_in_element

class AMTServer(object):
	SERVICE_TYPE_SANDBOX    = "sandbox"
	SERVICE_TYPE_PRODUCTION = "production"
	VALID_SERVICE_TYPES     = (SERVICE_TYPE_SANDBOX, SERVICE_TYPE_PRODUCTION)
	_WSDL_SCHEMA_VERSION_NOTIFICATIONS = "2006-05-05"

	_PREVIEW_HIT_TYPE_URL_STEMS = {
		"production":"http://mturk.com/mturk/preview?groupId=",
		"sandbox":"http://workersandbox.mturk.com/mturk/preview?groupId="
	}

	def __init__( self, aws_account_id, aws_account_key, service_type):
		assert service_type in self.VALID_SERVICE_TYPES
		self._server = AMTServerConnection(aws_account_id, aws_account_key, service_type)
		self._service_type = service_type

	@property
	def preview_hit_type_url_stem(self):
		return self._PREVIEW_HIT_TYPE_URL_STEMS[self._service_type]

	def do_request( self, operation, specific_parameters):
		return self._server.do_request(operation, specific_parameters)

	def grant_bonus(self, assignment_id, worker_id, amount, currency, reason):
		params = {
			"AssignmentId":assignment_id,
			"WorkerId":worker_id,
			"BonusAmount.1.Amount":amount,
			"BonusAmount.1.CurrencyCode":currency
		}
		if reason is not None:
			params["Reason"] = reason
		self._server.do_request( "GrantBonus", params)

	def create_hit(self, hit_type_id, question_xml, lifetime_in_seconds, max_assignments, requester_annotation, unique_request_token):
		kwargs = {
			"HITTypeId" : hit_type_id,
			"Question" : question_xml,
			"LifetimeInSeconds" : lifetime_in_seconds,
			"MaxAssignments" : max_assignments,
			"RequesterAnnotation" : requester_annotation,
			"ResponseGroup.0":"HITDetail",
			"ResponseGroup.1":"HITQuestion",
			"ResponseGroup.2":"Minimal",
			"ResponseGroup.3":"HITAssignmentSummary"
		}
		if unique_request_token is not None and unique_request_token != "":
			if not is_string(unique_request_token):
				raise ValueError("unique_request_token must be a string.  Got a %r."%type(unique_request_token))

			if len(unique_request_token) > 64:
				raise ValueError("unique_request_token should be <=64 characters.  Got %d characters."%len(unique_request_token))

			kwargs["UniqueRequestToken"] = unique_request_token

		dom = self._server.do_request( "CreateHIT", kwargs)
		hit_nodes = dom.getElementsByTagName("HIT")
		assert len(hit_nodes)==1
		hit_node = hit_nodes[0]
		result = self._extract_hit_node(hit_node=hit_node)
		return result

	def register_hit_type(self, title, description, reward, currency, time_limit, keywords, autopay_delay,
						qualification_requirements):
		keywords = to_tuple_if_non_sequence_iterable(keywords)
		qualification_requirements = to_tuple_if_non_sequence_iterable(qualification_requirements)
		assert is_string(title)
		assert is_string(description)
		assert is_number(reward)
		assert is_string(currency)
		assert isinstance(time_limit, datetime.timedelta)
		assert is_sequence_of_strings(keywords)
		assert isinstance(autopay_delay, datetime.timedelta)
		assert is_sequence_of(qualification_requirements, QualificationRequirement)

		params = {  "Title": title,
					"Description" : description,
					"Reward.1.Amount" : reward,
					"Reward.1.CurrencyCode" : currency,
					"AssignmentDurationInSeconds" : total_seconds(time_limit),
					"Keywords" : ",".join(keywords),
					"AutoApprovalDelayInSeconds" : total_seconds(autopay_delay)
				}

		# Add in parameters for any qualification_requirement requirements.
		for i,qualification_requirement in enumerate(qualification_requirements):
			params['QualificationRequirement.%d.QualificationTypeId'%(i+1)] = qualification_requirement.qualification_type_id
			params['QualificationRequirement.%d.Comparator'%(i+1)] = qualification_requirement.comparator

			if qualification_requirement.integer_value is not None:
				params['QualificationRequirement.%d.IntegerValue'%(i+1)] = str(qualification_requirement.integer_value)
			if qualification_requirement.locale_value is not None:
				params['QualificationRequirement.%d.LocaleValue.Country'%(i+1)] = qualification_requirement.locale_value

		# Send the request to AMT.
		dom = self._server.do_request( "RegisterHITType", params)

		# Get the HIT Type ID out of the response.
		hit_type_id = dom.getElementsByTagName("HITTypeId")[0].childNodes[0].data
		return hit_type_id


	def search_hits(self):
		page_num = 0
		page_size = 100
		request_params =  {
				"PageSize":page_size,
				"SortProperty":"Enumeration",
				"PageNumber":page_num,
				"ResponseGroup.0":"HITDetail",
				"ResponseGroup.1":"HITQuestion",
				"ResponseGroup.2":"Minimal",
				"ResponseGroup.3":"HITAssignmentSummary"
		}
		results = []
		while True:
			page_num += 1
			request_params["PageNumber"] = page_num
			dom = self._server.do_request("SearchHITs", request_params)

			total_num_results = int(text_in_element(dom,"TotalNumResults"))
			observed_page_num = int(text_in_element(dom,"PageNumber"))
			if page_num != observed_page_num:
				raise XMLProcessingException("Reported page number doesn't match expected")

			hit_nodes = dom.getElementsByTagName("HIT")
			for hit_node in hit_nodes:
				result = self._extract_hit_node(hit_node=hit_node)
				results.append(result)

			if total_num_results <= page_num*page_size:
				break
		return results
	
	def get_hit(self, hit_id):
		params = {
			"HITId":hit_id,
			"ResponseGroup.0":"HITDetail",
			"ResponseGroup.1":"HITQuestion",
			"ResponseGroup.2":"Minimal",
			"ResponseGroup.3":"HITAssignmentSummary"
		}
		dom = self._server.do_request( "GetHIT", params)
		hit_nodes = dom.getElementsByTagName("HIT")
		assert len(hit_nodes)==1
		hit_node = hit_nodes[0]
		result = self._extract_hit_node(hit_node=hit_node)
		return result

	def get_reviewable_hit_ids(self, hit_type_id=None): # GENERATOR
		page_num = 0
		page_size = 100
		request_params =  {"PageSize":page_size, "SortProperty":"Enumeration", "PageNumber":page_num}
		if hit_type_id is not None:
			request_params["HITTypeId"] = hit_type_id
		while True:
			page_num += 1
			assert page_num < 100000 # safe upper bound
			request_params["PageNumber"] = page_num
			dom = self.do_request("GetReviewableHITs", request_params)
			total_num_results = int( dom.getElementsByTagName("TotalNumResults")[0].childNodes[0].data )
			page_num_reported = int( dom.getElementsByTagName("PageNumber")[0].childNodes[0].data )
			assert page_num_reported==page_num

			for hit_id_node in dom.getElementsByTagName("HITId"):
				hit_id = str( hit_id_node.childNodes[0].data )
				yield hit_id

			if total_num_results <= page_num*page_size:
				break

	def unblock_worker_id( self, worker_id, reason ):
		if reason is None:
			# TODO: Refactor to AMTServer
			self._server.do_request("UnblockWorker", {"WorkerId" : worker_id})
		else:
			# TODO: Refactor to AMTServer
			self._server.do_request("UnblockWorker", {"WorkerId" : worker_id, "Reason" : reason})

	def extend_hit_id(self, hit_id, max_assignments_increment=0, expiration_increment=0):
		assert isinstance(max_assignments_increment, int) and max_assignments_increment >= 0
		assert isinstance(expiration_increment, int)      and expiration_increment >= 0
		assert max_assignments_increment>0  or  expiration_increment>0
		params = {"HITId": hit_id}
		if max_assignments_increment>0:
			params["MaxAssignmentsIncrement"] = int(round(max_assignments_increment,0))
		if expiration_increment>0:
			params["ExpirationIncrementInSeconds"] = int(round(expiration_increment,0))
		# TODO: Refactor to AMTServer
		self._server.do_request("ExtendHIT", params )
	
	def _extract_reward_node(self, reward_node):
		reward_info = {}
		for child in reward_node.childNodes:
			child_name = child.nodeName
			assert child_name in ("Amount","CurrencyCode","FormattedPrice")
			reward_info[child_name] = child.childNodes[0].data

		reward_node_info = Reward(
							amount=reward_info["Amount"],
							currency_code=reward_info["CurrencyCode"],
							formatted_price=reward_info["FormattedPrice"])
		return reward_node_info
	
	def _extract_qualification_requirement_node(self, qreq_node):
		qreq_info = {}
		assert qreq_node.nodeName=="QualificationRequirement"

		for child in qreq_node.childNodes:
			if child.nodeName=="LocaleValue":
				country_node = child.childNodes[0]
				assert country_node.nodeName=="Country"
				qreq_info["LocaleValue"] = text_node_content(country_node)
			else:
				# Common case
				qreq_info[child.nodeName] = text_node_content(child)

		qreq_node_info = QualificationRequirementRecord(
				qualification_type_id=qreq_info["QualificationTypeId"],
				comparator=qreq_info["Comparator"],
				integer_value=qreq_info.get("IntegerValue",None),
				locale_value=qreq_info.get("LocaleValue",None),
				required_to_preview=to_boolean(qreq_info["RequiredToPreview"]))

		return qreq_node_info


	def _extract_hit_node(self, hit_node):
		# SearchHITs does not return qualification requirements and possibly other attributes.
		# GetHIT might not return NumberOfAssignmentsCompleted and some others.  Not sure yet.

		kwargs = {}
		kwargs["qualification_requirements"] = []
		kwargs["hit_review_status"] = None
		kwargs["number_of_similar_hits"] = None
		kwargs["requester_annotation"] = ""

		keys_preppers_by_child_name = {
			"HITId": ("hit_id", None),
			"HITTypeId": ("hit_type_id", None),
			"CreationTime": ("creation_time", parse_iso_utc_to_datetime_local),
			"Title": ("title", None),
			"Description": ("description", None),
			"Question": ("question", None),
			"Keywords": ("keywords", lambda content:tuple(kw.strip() for kw in content.split(","))),
			"HITStatus": ("hit_status", None),
			"MaxAssignments": ("max_assignments", int),
			"AutoApprovalDelayInSeconds": ("auto_approval_delay", to_duration),
			"Expiration": ("expiration_time", parse_iso_utc_to_datetime_local),
			"AssignmentDurationInSeconds": ("assignment_duration", to_duration),
			"NumberOfSimilarHITs": ("number_of_similar_hits", int),
			"HITReviewStatus": ("hit_review_status", None),
			"RequesterAnnotation": ("requester_annotation", None),
			"NumberOfAssignmentsPending": ("num_pending", int),
			"NumberOfAssignmentsAvailable": ("num_available", int),
			"NumberOfAssignmentsCompleted": ("num_completed", int),
		}
		for child in hit_node.childNodes:
			child_name = child.nodeName

			if child_name=="Reward":
				kwargs["reward"] = self._extract_reward_node(child)
			elif child_name=="QualificationRequirement" and len(child.childNodes)>1:
				qreq = self._extract_qualification_requirement_node(child)
				kwargs["qualification_requirements"].append(qreq)
			elif child_name=="Request":
				pass # Ignore this one.
			elif child_name in ("HITGroupId", "HITLayoutId"):
				pass # not supported, ignore for now
			else:
				key,prepper_fn = keys_preppers_by_child_name[child_name] # KeyError here would indicate unexpected info in HIT structure
				content = text_node_content(child)
				if prepper_fn is not None:
					content = prepper_fn(content)
				kwargs[key] = content
		
		kwargs = dict((str(k),v) for (k,v) in kwargs.items())
		return HITRecord(**kwargs)

	def force_expire_hit( self, hit_id ):
		self._server.do_request( "ForceExpireHIT", {"HITId":hit_id} )

	def reject_assignment(self, assignment, reason):
		# reason may be None
		try:
			if reason is None:
				self._server.do_request( "RejectAssignment", {"AssignmentId":assignment.id} )
			else:
				self._server.do_request( "RejectAssignment", {"AssignmentId":assignment.id, "RequesterFeedback":reason} )
		except AMTRequestFailed:
			e = sys.exc_info()[1]
			if e.code=="AWS.MechanicalTurk.InvalidAssignmentState" and e.operation=="RejectAssignment":
				raise AssignmentAlreadyFinalizedException(assignment.id, assignment.assignment_status)
			else:
				raise
			
	def get_account_balance( self ):
		dom = self._server.do_request( "GetAccountBalance", {} )
		available_balance = float(text_in_element(dom,"Amount"))
		currency = text_in_element(dom, "CurrencyCode")
		formatted_price = text_in_element(dom, "FormattedPrice")
		amount = Reward(amount=available_balance, currency_code=currency, formatted_price=formatted_price)
		return amount

	def approve_assignment(self, assignment, requester_feedback):
		# requester_feedback may be None
		try:
			if requester_feedback is None:
				self._server.do_request( "ApproveAssignment", {"AssignmentId":assignment.id} )
			else:
				self._server.do_request( "ApproveAssignment", {"AssignmentId":assignment.id, "RequesterFeedback":requester_feedback} )
		except AMTRequestFailed:
			e = sys.exc_info()[1]
			if e.code=="AWS.MechanicalTurk.InvalidAssignmentState" and e.operation=="ApproveAssignment":
				raise AssignmentAlreadyFinalizedException(assignment.id, assignment.assignment_status)
			else:
				raise
	

	def create_qualification_type( self, name, description, initially_active, keywords, retry_delay, test_xml,
			                                 answer_key_xml, test_duration, auto_granted, auto_granted_value):
		assert isinstance(retry_delay, datetime.timedelta), retry_delay
		assert isinstance(test_duration, datetime.timedelta)
		param_pairs = (	( "Name", name ),
						( "Description", description ),
						( "Keywords", ",".join(keywords) ),
						( "RetryDelayInSeconds", total_seconds(retry_delay)),
						( "QualificationTypeStatus", ("Active" if initially_active else "Inactive") ),
						( "Test", test_xml ),
						( "AnswerKey", answer_key_xml ),
						( "TestDurationInSeconds", total_seconds(test_duration)),
						( "AutoGranted", ("true" if auto_granted else "false") ) )
		if auto_granted:
			param_pairs += (( "AutoGrantedValue", auto_granted_value ),)
		params = dict((k,v) for (k,v) in param_pairs if v is not None)
		dom = self._server.do_request( "CreateQualificationType", params )
		qtype_id = text_in_element( dom, "QualificationTypeId" )
		return qtype_id

	def get_qualification_types(self):
		# TODO: Refactor to AMTServer
		dom = self._server.do_request( "SearchQualificationTypes", {
			"MustBeRequestable" : "false",
			"MustBeOwnedByCaller" : "true",
			"PageSize" : "100",
			})
		num_results = int( text_in_element( dom, "NumResults" ) )
		assert num_results<100, "This code needs revision to handle >100 qualification types."
		results = []
		for node in dom.getElementsByTagName( "QualificationType" ):
			qtype_id = text_in_element(node, "QualificationTypeId")
			creation_time = datetime_in_element(node, "CreationTime")
			name = text_in_element(node, "Name")
			description = text_in_element(node, "Description")
			keywords = text_in_element(node, "Keywords")
			keywords = tuple(s.strip() for s in keywords.split(","))
			try:
				is_active = bool_in_element(node, "QualificationTypeStatus",
										value_if_true="Active", value_if_false="Inactive")
			except XMLProcessingException:
				is_active = None
			try:
				retry_delay = text_in_element(node, "RetryDelayInSeconds")
			except XMLProcessingException:
				retry_delay = None
			test_node = node.getElementsByTagName("Test")[0]
			# question_node = test_node.firstChild # removed this 10-8-2011.  Why was this needed before?
			test_xml = text_node_content(test_node)
			test_duration = duration_in_element(node, "TestDurationInSeconds")
			try:
				answer_key_xml = xml_in_element(node, "AnswerSpecification")
			except XMLProcessingException:
				answer_key_xml = None
			try:
				auto_granted = bool_in_element(node, "AutoGranted")
			except XMLProcessingException:
				auto_granted = None
			try:
				auto_granted_value = number_in_element(node, "AutoGrantedValue")
			except XMLProcessingException:
				auto_granted_value = None
			try:
				is_requestable = bool_in_element(node, "IsRequestable")
			except XMLProcessingException:
				is_requestable = None

			assert is_requestable == True or is_requestable is None # Notify Alex Quinn if this ever happens.  I don't think it will.
			# IsRequestable (is_requestable) should be True for any qualification requirement I created.
			# "Specifies whether the Qualification type is one that a user can request through the
			#  Amazon Mechanical Turk web site, such as by taking a Qualification test. This value is
			#  false for Qualifications assigned automatically by the system."
			# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationTypeDataStructureArticle.html

			if is_requestable is None:
				is_requestable = True # not sure why this would ever happen

			qtype = QualificationType(id=qtype_id,
									  creation_time=creation_time,
									  name=name,
									  description=description,
									  keywords=keywords,
									  is_active=is_active,
									  retry_delay=retry_delay,
									  test_xml=test_xml,
									  test_duration=test_duration,
									  answer_key_xml=answer_key_xml,
									  auto_granted=auto_granted,
									  auto_granted_value=auto_granted_value,
									  is_requestable=is_requestable)
			results.append( qtype )
		return results

	def notify_workers(self, worker_ids, subject, message_text):
		assert 1 <= len(worker_ids) <= 100
		params = {
			"Subject" : subject,
			"MessageText" : message_text
		}
		for j,worker_id in enumerate(worker_ids):
			params["WorkerId.%d"%(j+1)] = worker_id
		self._server.do_request("NotifyWorkers", params)

	def get_assignments_for_hit(self, hit):  # GENERATOR
		dom = self._server.do_request( "GetAssignmentsForHIT", {"HITId":hit.id, "PageSize":100, "PageNumber":1} )
		for assignment_node in dom.getElementsByTagName( "Assignment" ):
			assignment_record = self._extract_assignment_data( assignment_node=assignment_node )
			assert hit.id==assignment_record.hit_id, "Expected them to be the same: "%(repr((hit.id,assignment_record.hit_id)))
			yield assignment_record

	def _extract_assignment_data( self, assignment_node):
		autopay_time = rejection_time = submit_time = approval_time =  None

		answer_xml = None
		answer_records = ()
		requester_feedback = None
		for node in assignment_node.childNodes:
			name = node.nodeName
			if name=="AssignmentId":
				assignment_id = text_node_content( node )
			elif name=="WorkerId":
				worker_id = text_node_content( node )
				assert is_string(worker_id)
			elif name=="HITId":
				hit_id = text_node_content( node )
			elif name=="AssignmentStatus":
				assignment_status = text_node_content( node )
			elif name=="AutoApprovalTime":
				autopay_time = parse_iso_utc_to_datetime_local( text_node_content( node ) )
			elif name=="SubmitTime":
				submit_time = parse_iso_utc_to_datetime_local( text_node_content( node ) )
			elif name=="ApprovalTime":
				approval_time = parse_iso_utc_to_datetime_local( text_node_content( node ) )
			elif name=="AcceptTime":
				accept_time = parse_iso_utc_to_datetime_local( text_node_content( node ) )
			elif name=="RejectionTime":
				rejection_time = parse_iso_utc_to_datetime_local( text_node_content( node ) )
			elif name=="RequesterFeedback":
				requester_feedback = text_node_content( node )
			elif name=="Answer":
				assert answer_xml is None, "Only expected one Answer node per Assignment node"
				answer_xml = text_node_content( node )
				answer_dom = xml2dom(answer_xml)
				answer_dom_nodes = answer_dom.getElementsByTagName("Answer")
				answer_records = tuple(self._extract_answer_from_dom_node(node) for node in answer_dom_nodes)

		assignment_record = AssignmentRecord(
				accept_time=accept_time,
				answer_records=answer_records,
				approval_time=approval_time,
				assignment_id=assignment_id,
				assignment_status=assignment_status,
				auto_approval_time=autopay_time,
				hit_id=hit_id,
				rejection_time=rejection_time,
				requester_feedback=requester_feedback,
				submit_time=submit_time,
				worker_id=worker_id)

		return assignment_record


	def get_requester_statistic(self, statistic, time_period, count=None):
		# Details at:
		# http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/ApiReference_GetRequesterStatisticOperation.html
		# The max count is 730.  Discovered by experiment on 2-14-2011.
		assert time_period in ("OneDay", "SevenDays", "ThirtyDays", "LifeToDate"), time_period
		assert statistic in ("NumberAssignmentsAvailable", "NumberAssignmentsAccepted", 
				"NumberAssignmentsPending", "NumberAssignmentsApproved", "NumberAssignmentsRejected", 
				"NumberAssignmentsReturned", "NumberAssignmentsAbandoned", "PercentAssignmentsApproved", 
				"PercentAssignmentsRejected", "TotalRewardPayout", "AverageRewardAmount",
				"TotalRewardFeePayout", "TotalFeePayout", "TotalRewardAndFeePayout", "TotalBonusPayout", 
				"TotalBonusFeePayout", "NumberHITsCreated", "NumberHITsCompleted", "NumberHITsAssignable", 
				"NumberHITsReviewable", "EstimatedRewardLiability", "EstimatedFeeLiability", 
				"EstimatedTotalLiability")

		assert not (statistic=="NumberHITsAssignable" and time_period!="LifeToDate")
		# NumberHITsAssignable may not be collected on a daily basis.  See note in docs:
		# http://docs.amazonwebservices.com/AWSMechTurk/2008-08-02/AWSMturkAPI/ApiReference_GetRequesterStatisticOperation.html

		assert (time_period=="LifeToDate") ^ (isinstance(count,int))  # need count iff time_period is anything other than LifeToDate

		params = {
				"Statistic" : statistic,
				"TimePeriod" : time_period
		}
		if count is not None:
			params["Count"] = count
			assert time_period=="OneDay", "Count can only be specified if the time period is OneDay" # per docs
		dom = self._server.do_request("GetRequesterStatistic", params)
		nodes = dom.getElementsByTagName("DataPoint")
		assert len(nodes)==1 or (time_period=="OneDay" and len(nodes)>=1)
		results = []
		for node in nodes:
			date = parse_iso_utc_to_datetime_local(text_in_element(node, "Date"))
			if statistic.startswith("Number"):
				val  = int(text_in_element(node, "LongValue"))
			else:
				val = float(text_in_element(node, "DoubleValue"))
			results.append((date,val))
		return results


	def _extract_answer_from_dom_node( self, answer_node):

		free_text = uploaded_file_key = uploaded_file_size_in_bytes = selection_identifier = other_selection = None

		for answer_child_node in answer_node.childNodes:
			answer_child_name = answer_child_node.nodeName
			if answer_child_name=="QuestionIdentifier":
				question_identifier = to_unicode( text_node_content( answer_child_node ) )
			elif answer_child_name == "FreeText":
				free_text = to_unicode( text_node_content( answer_child_node ) )
			elif answer_child_name == "SelectionIdentifier":
				selection_identifier = to_unicode( text_node_content( answer_child_node ) )
			elif answer_child_name == "OtherSelection":
				other_selection = to_unicode( text_node_content(answer_child_node ) )
			elif answer_child_name == "UploadedFileKey":
				uploaded_file_key = to_unicode( text_node_content( answer_child_node ) )
			elif answer_child_name == "UploadedFileSizeInBytes":
				uploaded_file_size_in_bytes = int( text_node_content( answer_child_node ) )
			elif answer_child_name=="#text":
				pass
			else:
				assert False, "Unexpected node type found: %s"%answer_child_name

		answer_record = AnswerRecord(
				question_identifier=question_identifier,
				free_text=free_text,
				selection_identifier=selection_identifier,
				other_selection=other_selection,
				uploaded_file_key=uploaded_file_key,
				uploaded_file_size_in_bytes=uploaded_file_size_in_bytes)

		return answer_record

	NOTIFICATION_EVENT_TYPE_ASSIGNMENT_ACCEPTED  = "AssignmentAccepted"
	NOTIFICATION_EVENT_TYPE_ASSIGNMENT_ABANDONED = "AssignmentAbandoned"
	NOTIFICATION_EVENT_TYPE_RETURNED             = "AssignmentReturned"
	NOTIFICATION_EVENT_TYPE_SUBMITTED            = "AssignmentSubmitted"
	NOTIFICATION_EVENT_TYPE_REVIEWABLE           = "HITReviewable"
	NOTIFICATION_EVENT_TYPE_EXPIRED              = "HITExpired"
	NOTIFICATION_EVENT_TYPES_ALL = (NOTIFICATION_EVENT_TYPE_ASSIGNMENT_ACCEPTED,
									NOTIFICATION_EVENT_TYPE_ASSIGNMENT_ABANDONED,
									NOTIFICATION_EVENT_TYPE_RETURNED,
									NOTIFICATION_EVENT_TYPE_SUBMITTED,
									NOTIFICATION_EVENT_TYPE_REVIEWABLE,
									NOTIFICATION_EVENT_TYPE_EXPIRED)

	def set_hit_type_notification(self, hit_type_id, address, transport, event_types):
		params = {	"HITTypeId" : hit_type_id,
					"Notification.1.Destination" : address,
					"Notification.1.Transport"   : transport,
					"Notification.1.Version"     : self._WSDL_SCHEMA_VERSION_NOTIFICATIONS,
					"Notification.1.Active"      : "true" }

		if len(event_types) == 1:
			params["Notification.1.EventType"] = event_types[0]
		else:
			i = 0
			for event_type in event_types:
				i += 1 # should start with 1
				params["Notification.1.EventType.%d"%i] = event_type

		self._server.do_request("SetHITTypeNotification", params)

	def send_test_event_notification(self, address, transport, event_type):
		if event_type not in self.NOTIFICATION_EVENT_TYPES_ALL:
			raise ValueError("event_type %s is supposed to be one of %s"%(event_type, repr(self.NOTIFICATION_EVENT_TYPES_ALL)))
		params = {	"Notification.1.Destination" : address,
					"Notification.1.Transport"   : transport,
					"Notification.1.EventType"   : event_type,
					"Notification.1.Version"     : self._WSDL_SCHEMA_VERSION_NOTIFICATIONS,
					"Notification.1.Active"      : "true",
					"TestEventType"              : event_type,
					}
		self._server.do_request("SendTestEventNotification", params)

	def set_hit_type_notification_inactive(self, hit_type_id):
		params = {	"HITTypeId" : hit_type_id,
				    "Active" : "false" }
		self._server.do_request("SetHITTypeNotification", params)
	
	def get_file_upload_url(self, assignment_id, question_id):
		params = {  "AssignmentId" : assignment_id,
					"QuestionIdentifier" : question_id }
		dom = self._server.do_request("GetFileUploadURL", params)
		url = text_in_element(dom, "FileUploadURL")
		return url



#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# EXPERIEMENTAL CODE (do not delete, yet)
#

#	TODO:  Make search_hits multi-threaded.  Below is a start on doing that.
#
#	There are some options.  I'm not sure which is best, easiest, or even possible/functional:
#	  * worker threads
#	  * asynchttp module
#	  * pycurl
#	  * eventlets / greenlets
#	  * concurrent futures
#
#	The advantage of threads is that it would pose no serious Python 2/3 or platform issues.  However,
#	someone said in this StackOverflow discussion that threads may not solve the problem.
#	http://stackoverflow.com/questions/4962808/asynchronous-http-calls-in-python#comment21544074_4963126
#
#	def search_hits(self):
#		# Strategy:  Use a queue and worker threads.
#
#		# MULTI-THREADED
#		from crowdlib.all_exceptions import XMLProcessingException
#		from crowdlib.utility import text_in_element, dmp_xml
#		from math import ceil
#		page_num = 0
#		page_size = 100
#		request_params =  {"PageSize":page_size, "SortProperty":"Enumeration", "PageNumber":page_num, "ResponseGroup.0":"HITDetail", "ResponseGroup.1":"HITQuestion","ResponseGroup.2":"Minimal","ResponseGroup.3":"HITAssignmentSummary"}
#		hits_seen = 0
#		hit_type_dict = {}
#
#		# Page number is 1-based.
#		# http://docs.amazonwebservices.com/AWSMechTurk/2008-08-02/AWSMturkAPI/ApiReference_SearchHITsOperation.html
#
#		first_page_num = 1
#		request_params["PageNumber"] = first_page_num
#		operation = "SearchHITs"
#		dom = self._server.do_request(operation, request_params)
#		doms = [dom]
##			num_results = int(text_in_element(dom, "NumResults"))
#		total_num_results = int(text_in_element(dom,"TotalNumResults"))
##			observed_page_num = int(text_in_element(dom,"PageNumber"))
##			if page_num != observed_page_num:
##				raise XMLProcessingException("Reported page number doesn't match expected")
#		num_pages = int(ceil(total_num_results / page_size))	
#		operation_specific_parameters_pairs = []
#		for page_num in range(first_page_num + 1, first_page_num + num_pages):
#			request_params = request_params.copy()
#			request_params["PageNumber"] = page_num
#			operation_specific_parameters_pairs.append((operation, request_params))
#
#		doms += self._server.do_requests_simultaneously(operation_specific_parameters_pairs=operation_specific_parameters_pairs)
#		for dom in doms:
#			hit_nodes = dom.getElementsByTagName("HIT")
#			for hit_node in hit_nodes:
#				result = self._extract_hit_node(hit_node=hit_node)
#				yield result
	


#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# SHRAPNEL (delete any time if you don't think it will be needed)
#

#		kwargs["hit_type_id"]=hit_info["HITTypeId"]
#		kwargs["creation_time"] = to_date_time( hit_info["CreationTime"] )
#		kwargs["title"]=hit_info["Title"]
#		kwargs["keywords"]=tuple(hit_info.get("Keywords","").split(","))
#		kwargs["description"]=hit_info["Description"]
#		kwargs["hit_status"]=hit_info["HITStatus"]
#		kwargs["currency"]=hit_info["Reward.CurrencyCode"]
#		kwargs["time_limit"]=to_duration(hit_info["AssignmentDurationInSeconds"]
#		kwargs["autopay_delay"]=to_duration(hit_info["AutoApprovalDelayInSeconds"]
#
#		if expect_partial:
#			hit_node_partial_info = SearchHITsResult(
#				hit_id=hit_id,
#				hit_type_id=hit_type_id,
#				title=title,
#				description=description,
#				creation_time=creation_time,
#				expiration_time=expiration_time,
#
#							hit_id=hit_info["HITId"],
#							hit_type_id=hit_info["HITTypeId"],
#							creation_time = to_date_time( hit_info["CreationTime"] )
#							title=to_unicode(hit_info["Title"]),
#							description=to_unicode(hit_info["Description"]),
#						    hit_status=hit_info["HITStatus"],
#
#							reward=float(hit_info["Reward.Amount"]),
#							currency=to_unicode( hit_info["Reward.CurrencyCode"] ),
#							time_limit=to_duration(hit_info["AssignmentDurationInSeconds"]),
#							autopay_delay=to_duration(hit_info["AutoApprovalDelayInSeconds"]),
#							keywords=keywords,
#							qualification_requirements=qualification_requirements,
#							details=details,
#							amt=self)
#					hit_id)
#		hit_type_id = to_unicode(hit_info["HITTypeId"])
#		keywords=tuple(to_unicode(kw) for kw in hit_info.get("Keywords","").split(","))
#		details = {}  # Details aren't stored on server, so if we don't have them, we're out of luck.
#		hit_type = HITType( id=hit_type_id,
#							title=to_unicode(hit_info["Title"]),
#							description=to_unicode(hit_info["Description"]),
#							reward=float(hit_info["Reward.Amount"]),
#							currency=to_unicode( hit_info["Reward.CurrencyCode"] ),
#							time_limit=to_duration(hit_info["AssignmentDurationInSeconds"]),
#							autopay_delay=to_duration(hit_info["AutoApprovalDelayInSeconds"]),
#							keywords=keywords,
#							qualification_requirements=qualification_requirements,
#							details=details,
#							amt=self)
#		self._db.put_hit_type(hit_type)
#		assert hit_type_id not in self._hit_type_dict
#		self._hit_type_dict[hit_type_id] = hit_type
#		return hit_type

#	def _extract_hit_type_from_hit_node(self, hit_node):
#		'''
#		@warning:  SearchHITs does not return the qualification requirements.  Make sure
#				   to pass results from GetHIT, not SearchHITs, into this.
#		'''
#		from crowdlib.utility import to_unicode, to_date_time
#		from crowdlib.QualificationRequirement import QualificationRequirement
#		parts_of_interest = ("HITTypeId", "Title", "Description", "Keywords",
#				"AssignmentDurationInSeconds", "Reward",
#				"AutoApprovalDelayInSeconds", "QualificationRequirement")
#
#		hit_info = {}
#		qualification_requirements = []
#		for child in hit_node.childNodes:
#			child_name = child.nodeName
#
#			if child_name=="Reward":
#			# Use dot notation for the reward since it has subnodes.
#				for reward_child in child.childNodes:
#					reward_child_name = reward_child.nodeName
#					if reward_child_name in ( "Amount","CurrencyCode","FormattedPrice" ):
#						hit_info["Reward" + "." + reward_child_name] = reward_child.childNodes[0].data
#			elif child_name=="QualificationRequirement" and len(child.childNodes)>1:
#				qid   = text_in_element(child, "QualificationTypeId")
#				qcomp = text_in_element(child, "Comparator")
#				try:
#					qintval  = int(text_in_element(child, "IntegerValue"))
#					qlocaleval = None
#				except XMLProcessingException:
#					qlocaleval  = int(text_in_element(child, "LocaleValue"))
#					qintval = None
#
#				qualification_requirement = QualificationRequirement(
#						qualification_type_id=qid,
#						comparator=qcomp,
#						integer_value=qintval,
#						locale_value=qlocaleval,
#						required_to_preview=False)
#				qualification_requirements.append(qualification_requirement)
#				#hit_info["QualificationTypeId"] = text_in_element( child, "QualificationTypeId" )
#			elif child_name in parts_of_interest:
#				try:
#					contents = child.childNodes[0].data
#				except IndexError: # Why???? (11-15-2010)
#					contents = ""
#				hit_info[child_name] = contents
#
#		hit_type_id = to_unicode(hit_info["HITTypeId"])
#		keywords=tuple(to_unicode(kw) for kw in hit_info.get("Keywords","").split(","))
#		details = {}  # Details aren't stored on server, so if we don't have them, we're out of luck.
#		hit_type = HITType( id=hit_type_id,
#							title=to_unicode(hit_info["Title"]),
#							description=to_unicode(hit_info["Description"]),
#							reward=float(hit_info["Reward.Amount"]),
#							currency=to_unicode( hit_info["Reward.CurrencyCode"] ),
#							time_limit=to_duration(hit_info["AssignmentDurationInSeconds"]),
#							autopay_delay=to_duration(hit_info["AutoApprovalDelayInSeconds"]),
#							keywords=keywords,
#							qualification_requirements=qualification_requirements,
#							details=details,
#							amt=self)
#		self._db.put_hit_type(hit_type)
#		assert hit_type_id not in self._hit_type_dict
#		self._hit_type_dict[hit_type_id] = hit_type
#		return hit_type

#	def _extract_from_hit_node( self, hit_node, hit_type, just_update_shell ):
#
#		from crowdlib.utility import to_unicode, to_date_time
#		parts_of_interest = (
#				"HITId", "HITTypeId", "CreationTime", "HITStatus", "MaxAssignments", "Expiration",
#				"RequesterAnnotation", "Question", "NumberOfAssignmentsPending",
#				"NumberOfAssignmentsAvailable", "NumberOfAssignmentsCompleted")
#
#		hit_info = {}
#		hit_info["HITReviewStatus"] = None
#		for child in hit_node.childNodes:
#			child_name = child.nodeName
#			if child_name in parts_of_interest:
#				try:
#					contents = to_unicode(child.childNodes[0].data)
#				except IndexError:  # Why???? (11-15-2010)
#					contents = ""
#				hit_info[child_name] = contents
#
#		assert to_unicode(hit_info["HITTypeId"]) == hit_type.id
#
#		hit_id = to_unicode(hit_info["HITId"])
#		details = {}  # Details aren't stored on server, so if we don't have them, we're out of luck.
#
#		# If we're just making a shell for an update, then pass None for amt
#		if just_update_shell:
#			amt = None
#		else:
#			amt = self
#
#		hit_status = hit_info["HITStatus"]
#		creation_time = to_date_time( hit_info["CreationTime"] )
#		expiration_time = to_date_time( hit_info["Expiration"] )
#		num_pending   = int( hit_info.get("NumberOfAssignmentsPending", 0) )
#		num_available = int( hit_info.get("NumberOfAssignmentsAvailable", 0) )
#		num_completed = int( hit_info.get("NumberOfAssignmentsCompleted", 0) )
#		hit_review_status = hit_info.get("HITReviewStatus", None)
#		max_assignments=int( hit_info["MaxAssignments"] )
#
#		
#		hit = HIT( id=hit_id,
#				   hit_type=hit_type,
#				   question_xml=hit_info.get("Question",None),
#				   max_assignments=max_assignments,
#				   requester_annotation=hit_info.get("RequesterAnnotation",""),
#				   creation_time = creation_time,
#				   hit_status = hit_status,
#				   expiration_time = expiration_time,
#				   num_pending   = num_pending,
#				   num_available = num_available,
#				   num_completed = num_completed,
#				   hit_review_status = hit_review_status,
#				   details=details,
#				   amt=amt)
#
#		if just_update_shell:
#			self._db.update_hit(hit_id=hit_id, hit_status=hit_status, creation_time=creation_time,
#					expiration_time=expiration_time, num_pending=num_pending, num_available=num_available,
#					num_completed=num_completed, max_assignments=max_assignments)
#		else:
#			self._db.put_hit(hit)
#			assert hit_id not in self._hit_dict, hit_id
#			self._hit_dict[hit_id] = hit
#
#		return hit

#	def get_bonus_payments(hit_id=None, assignment_id=None):
#		if not ((hit_id is None) ^ (assignment_id is None)):
#			raise ValueError("You must pass in one of hit_id or assignment_id, and "
#			                 "not both.  Received hit_id=%s and assignment_id=%s"%(
#						     repr(hit_id), repr(assignment_id)))
#		if hit_id is not None:
#			params = {"HITId":hit_id}
#		else:
#			params = {"AssignmentId":assignment_id}
#		params[""]
#		dom = self._server.do_request("GetBonusPayments", params)
		
#	def create_qualification_type(self, name, description, keywords, retry_delay, qualification_type_status,
#			test_xml, answer_key_xml, test_duration, auto_granted, auto_granted_value):
#		param_pairs = (	( "Name", name ),
#						( "Description", description ),
#						( "Keywords", ",".join(keywords) ),
#						( "RetryDelayInSeconds", total_seconds(retry_delay)),
#						( "QualificationTypeStatus", ("Active" if is_active else "Inactive") ),
#						( "Test", test_xml ),
#						( "AnswerKey", answer_key_xml ),
#						( "TestDurationInSeconds", total_seconds(test_duration)),
#						( "AutoGranted", ("true" if auto_granted else "false") ) )
#		if auto_granted:
#			param_pairs += (( "AutoGrantedValue", auto_granted_value ),)
#		params = dict((k,v) for (k,v) in param_pairs if v is not None)
#		try:
#			dom = self._server.do_request( "CreateQualificationType", params )

#	def search_hits(self):
#		from crowdlib.all_exceptions import XMLProcessingException
#		page_num = 0
#		page_size = 100
#		request_params =  {"PageSize":page_size, "SortProperty":"Enumeration", "PageNumber":page_num}
#		hits_seen = 0
#		hit_type_dict = {}
#		while True:
#			page_num += 1
#			request_params["PageNumber"] = page_num
#			dom = self._server.do_request("SearchHITs", request_params)
#			num_results = int(text_in_element(dom, "NumResults"))
#			total_num_results = int(text_in_element(dom,"TotalNumResults"))
#			observed_page_num = int(text_in_element(dom,"PageNumber"))
#			if page_num != observed_page_num:
#				raise XMLProcessingException("Reported page number doesn't match expected")
#
#			hit_nodes = dom.getElementsByTagName("HIT")
#			for hit_node in hit_nodes:
#				hit_info = {}
#				for child in hit_node.childNodes:
#					child_name = child.nodeName
#					if child_name=="Reward":
#					# Use dot notation for the reward since it has subnodes.
#						for reward_child in child.childNodes:
#							reward_child_name = reward_child.nodeName
#							if reward_child_name in ( "Amount","CurrencyCode","FormattedPrice" ):
#								hit_info["Reward" + "." + reward_child_name] = reward_child.childNodes[0].data
#					elif child_name=="QualificationRequirement" and len(child.childNodes)>1:
#						qid   = text_in_element(child, "QualificationTypeId")
#						qcomp = text_in_element(child, "Comparator")
#						try:
#							qintval  = int(text_in_element(child, "IntegerValue"))
#							qlocaleval = None
#						except XMLProcessingException:
#							qlocaleval  = int(text_in_element(child, "LocaleValue"))
#							qintval = None
#
#						qualification_requirement = QualificationRequirement(
#								qualification_type_id=qid,
#								comparator=qcomp,
#								integer_value=qintval,
#								locale_value=qlocaleval,
#								required_to_preview=False)
#						qualification_requirements.append(qualification_requirement)
#						#hit_info["QualificationTypeId"] = text_in_element( child, "QualificationTypeId" )
#					elif child_name in parts_of_interest:
#						try:
#							contents = child.childNodes[0].data
#						except IndexError: # Why???? (11-15-2010)
#							contents = ""
#						hit_info[child_name] = contents
#			for hit_node in hit_nodes:
#				hit_type_id = text_in_element(hit_node, "HITTypeId")
#				if hit_type_id in hit_type_dict:
#					hit_type = hit_type_dict[hit_type_id]
#
#					hit = self._extract_from_hit_node(hit_node, hit_type, just_update_shell=False)
#					# This will add it to the DB.
#
#				else:
#					hit_id = text_in_element(hit_node, "HITId")
#
#					assert False, "This is broken.  Won't return an actual HIT." #FIXME
#					hit = self.get_hit(hit_id)
#					# This will add it to the DB.
#
#					hit_type_dict[hit_type_id] = hit.hit_type
#
#			if total_num_results <= page_num*page_size:
#				break

# TAKEN FROM END OF _extract_assignment_data(..)
#		answers = []
#		assignment = Assignment(    id=assignment_id,
#									worker=worker,
#									hit=hit,
#									assignment_status=assignment_status,
#									autopay_time=autopay_time,
#									submit_time=submit_time,
#									approval_time=approval_time,
#									accept_time=accept_time,
#									rejection_time=rejection_time,
#									requester_feedback=requester_feedback,
#									answers=answers,
#									amt=amt)
#
#		# ***** CIRCULAR REFERENCE   *****
#		# WARNING:  We are creating a circular reference here.  The Assignment
#		# keeps a list of Answers, each of which maintains a reference back to
#		# the assignment.  We first feed the Assignment object with an empty list
#		# and then populate the list from the outside.
#
#		answer_dom = xml2dom(answer_xml)
#
#		for answer_node in answer_dom.getElementsByTagName("Answer"):
#			answer = self._extract_answer_from_dom_node( answer_node, assignment )
#			answers.append( answer )  # answers was given to assignment above.
#
#		if just_update_shell:
#			self._db.update_assignment(assignment_id=assignment_id, assignment_status=assignment_status,
#					submit_time=submit_time, approval_time=approval_time,
#					rejection_time=rejection_time, requester_feedback=requester_feedback)
#		else:
#			self._db.put_assignment(assignment)
#
#		return assignment
