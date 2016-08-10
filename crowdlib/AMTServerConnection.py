# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: November 2010
'''

from __future__ import division, with_statement
import codecs, hmac, os, pprint, sys, time, traceback
from crowdlib.all_exceptions import AMTQualificationTypeAlreadyExists, AMTRequestFailed
from crowdlib.utility import base64_encodestring_py23_compatible, clear_line, get_call_stack_strs, log, urlencode_py23_compatible, urlopen_py23_compatible, xml2dom
from crowdlib.utility.debugging import is_debugging
from crowdlib.utility.time_utils import now_local
from hashlib import sha1 as sha

VERBOSE = False
DEBUG_LOG_REQUESTS_TO_FILE = "~/.crowdlib_data/server_requests_log.py"

class AMTServerConnection(object):
	# Service types: sandbox and production
	SERVICE_TYPE_SANDBOX    = "sandbox"
	SERVICE_TYPE_PRODUCTION = "production"
	VALID_SERVICE_TYPES     = (SERVICE_TYPE_SANDBOX, SERVICE_TYPE_PRODUCTION)

	#_SERVICE_VERSION = '2008-08-02'
	_SERVICE_VERSION = '2012-03-25'
	_SERVICE_NAME = 'AWSMechanicalTurkRequester'

	_PREVIEW_HIT_TYPE_URL_STEMS = {
			"production":"http://mturk.com/mturk/preview?groupId=",
			"sandbox":"http://workersandbox.mturk.com/mturk/preview?groupId="
	}

	_SERVICE_URLS = {
			"sandbox"    : "https://mechanicalturk.sandbox.amazonaws.com/onca/xml?",
			"production" : 'https://mechanicalturk.amazonaws.com/onca/xml?'
	}

	def __init__( self, aws_account_id,
						aws_account_key,
						service_type):

		assert service_type in self.VALID_SERVICE_TYPES

		# Main SETTINGS
		self._aws_account_id = aws_account_id
		self._aws_account_key = aws_account_key
		self._service_type = service_type
		self._max_requests_per_second = {"sandbox":5, "production":100}[service_type]
		self._url = self._SERVICE_URLS[service_type] # URL for submitting requests to AMT
		self._last_request_time = None  # for dealing with AMT throttling

	@property
	def preview_hit_type_url_stem(self):
		return self._PREVIEW_HIT_TYPE_URL_STEMS[self._service_type]

	def _generate_timestamp(self,gmtime):
		#return  '2010-06-13T04:04:49Z'
		return time.strftime("%Y-%m-%dT%H:%M:%SZ", gmtime)

	def _generate_signature(self,service, operation, timestamp, secret_access_key):
		# Encoding to "ascii" is to make this work on either Python2 or Python3.  On v2.6 it just returns
		# the same string.  On v3.x, it returns a bytes object.
		my_sha_hmac = hmac.new(secret_access_key.encode("ascii"), (service + operation + timestamp).encode("ascii"), sha)

		my_b64_hmac_digest = base64_encodestring_py23_compatible(my_sha_hmac.digest()).strip()
		my_b64_hmac_digest = my_b64_hmac_digest.decode("ascii")
		return my_b64_hmac_digest

	# pylint: disable=R0912,R0915
	#         Tolerate too many branches and too many statements.
	def do_request( self, operation, specific_parameters):
		'''
		Run an AWS request.

		This method takes care of signing the request, submitting it to AWS via a REST call,
		managing load on AWS, and coping with small server and network errors that
		inevitably come up.  It can be used when you need to do something differently
		than CrowdLib provides.

		operation (str) : The AWS operation code (i.e., "CreateHIT")
		specific_parameters (dict) : All REST parameters except Service, Version, AWSAccessKeyId, Timestamp, Signature, and Operation.

		Returns (DOM object) : AMT's response as a DOM object created by the xml.dom.minidom module

		Note:  This does not currently deal with disposing of the DOM objects.
		'''

		_verbose = VERBOSE or is_debugging()
		if _verbose:
			dbg_before_time = time.time()
			msg =  "                                                              > "+operation 
			log(msg, should_terminate=False)

		self._last_request_time = time.time()

		# Parameters for quick retry (in case of throttling or minor network issues)
		query_retry_delay = 1.0 # seconds, also subject to exponential backoff (delay **= 1.5 each time)
		query_retry_delay_backoff_exponent = 1.5
		query_retry_delay_max = 60*5 # Don't stall longer than 15 minutes
		query_retry_count = int(60*60*24 / query_retry_delay_max)  # Give up after 24 hours.

		if DEBUG_LOG_REQUESTS_TO_FILE:
			formatted_traceback_if_exception = None

		# Start trying.  Normally, it will succeed on the first try... we hope.  :)
		for try_counter in range( query_retry_count ):
			try:
				result_xml = None
				errors_nodes = None
				timestamp = self._generate_timestamp(time.gmtime())
				signature = self._generate_signature('AWSMechanicalTurkRequester', operation, timestamp, self._aws_account_key)

				parameters = {
						'Service': self._SERVICE_NAME,
						'Version': self._SERVICE_VERSION,
						'AWSAccessKeyId': self._aws_account_id,
						'Timestamp': timestamp,
						'Signature': signature,
						'Operation': operation,
						}
				parameters.update( specific_parameters )

				# Make the request
				encoded_parameters = urlencode_py23_compatible(parameters)
				result_xml = urlopen_py23_compatible(self._url, encoded_parameters).read()
				result_dom = xml2dom(result_xml)

				errors_nodes = result_dom.getElementsByTagName('Errors')
				if errors_nodes:
					for errors_node in errors_nodes:
						for error_node in errors_node.getElementsByTagName('Error'):
							code = error_node.getElementsByTagName('Code')[0].childNodes[0].data
							msg  = error_node.getElementsByTagName('Message')[0].childNodes[0].data
							if code.endswith("AWS.MechanicalTurk.QualificationTypeAlreadyExists"):
								raise AMTQualificationTypeAlreadyExists(code, msg, operation, parameters.get("Name",""))
							else:
								raise AMTRequestFailed( code=code, msg=msg, operation=operation, query_params=specific_parameters )
				else:
					break
			except Exception:     # [pylint] blanket exception handler, will re-raise if not handled : pylint:disable=W0703
				e = sys.exc_info()[1]
				if DEBUG_LOG_REQUESTS_TO_FILE:
					formatted_traceback_if_exception = traceback.format_exc().splitlines()

				if isinstance(e, AMTRequestFailed):
					if not (operation=="ForceExpireHIT" and code.endswith("InvalidHITState")):
						pass
					if code in ("ServiceUnavailable", "AWS.ServiceUnavailable"):
						self._max_requests_per_second = max(0.01, self._max_requests_per_second-0.1)
					else:
						# Don't retry unknown AMT exceptions.
						raise e
				elif isinstance(e, IOError):
					pass
				elif try_counter+1 >= query_retry_count:
					raise e
				else:
					#import traceback
					#traceback.print_exc()
					raise e
				time.sleep( query_retry_delay )
				query_retry_delay = query_retry_delay ** query_retry_delay_backoff_exponent
				query_retry_delay = min(query_retry_delay, query_retry_delay_max)

				if DEBUG_LOG_REQUESTS_TO_FILE:
					formatted_traceback_if_exception = None  #If we get this far, then it was handled and need not be logged after all.

			finally:
				if _verbose or DEBUG_LOG_REQUESTS_TO_FILE:
					call_stack_strs = get_call_stack_strs(include_only_paths_starting_with="S:/d/")

					if DEBUG_LOG_REQUESTS_TO_FILE:
						self._write_to_request_log_file(operation, specific_parameters, call_stack_strs, formatted_traceback_if_exception)

		if _verbose:
			clear_line()
			elapsed_time = time.time() - dbg_before_time
			msg =  "                                                              > %s  in  %.5f seconds"%(operation, elapsed_time)
			#msg = msg + "\n".join("\n - %s"%s for s in reversed(call_stack_strs))
			log(msg)

		return result_dom

	def _write_to_request_log_file(self, operation, specific_parameters, call_stack_strs, formatted_traceback_if_exception):
		now = now_local()
		now_str = now.strftime("%Y%m%d-%H%M%S")
		path = os.path.expanduser(DEBUG_LOG_REQUESTS_TO_FILE)
		if not os.path.exists(path):
			s = "server_requests = []\n"
			s += "\n"
		else:
			s = ""
		s += "# " + "_"*80 + "\n"
		s += "# " + now_str + "\n"
		log_data = {
			"timestamp" : now_str,
			"service_type" : self._service_type,
			"aws_account_id" : self._aws_account_id,
			"last_request_time" : self._last_request_time,
			"operation" : operation,
			"specific_parameters" : specific_parameters,
			"call_stack_strs" : call_stack_strs,
		}
		if formatted_traceback_if_exception:
			log_data["traceback"] = formatted_traceback_if_exception
		s += "server_requests.append(" + pprint.pformat(log_data) + ")" + "\n"
		s += "\n"
		with codecs.open(path, "a", "utf8") as log_file:
			log_file.write(s)


#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# EXPERIEMENTAL CODE (do not delete, yet)
#

#	def do_requests_simultaneously( self, operation_specific_parameters_pairs ):
#
#		# Only do threading in production mode.  Sandbox doesn't like heavy load.
#
#		doms = []
#		if self._service_type==self.SERVICE_TYPE_PRODUCTION and False:
#			try:
#				# Python 2
#				from Queue import Queue, Empty
#			except ImportError:
#				# Python 3
#				from queue import Queue, Empty
#			import threading
#			num_worker_threads = 4
#
#			# Create a thread-safe queue and populate with the requests.
#			inputs = Queue()
#			results = Queue()
#
#			def worker():
#				operation,specific_parameters = inputs.get()
#				dom = self.do_request(operation=operation, specific_parameters=specific_parameters)
#				results.put(dom)
#				q.task_done()
#
#			for operation,specific_parameters in operation_specific_parameters_pairs:
#				inputs.put((operation,specific_parameters))
#
#			for i in range(num_worker_threads):
#				t = threading.Thread(target=worker)
#				t.daemon = True
#				t.start()
#
#			inputs.join()
#			try:
#				while True:
#					dom = results.get()
#					doms.append(dom)
#			except Empty:
#				pass
#		else:
#			for operation,specific_parameters in operation_specific_parameters_pairs:
#				dom = self.do_request(operation=operation, specific_parameters=specific_parameters)
#				doms.append(dom)
#		return doms


#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# SHRAPNEL (delete any time if you don't think it will be needed)
#

# ## taken from do_request() .. near top
#		# Rate limiting, but only in sandbox
#		if self._service_type == self.SERVICE_TYPE_SANDBOX:
#			if self._last_request_time is not None:
#				seconds_since_last_request = time.time()-self._last_request_time
#				required_interval = 1.0 / self._max_requests_per_second
#				if seconds_since_last_request < required_interval:
#					time.sleep( max( 0.01, required_interval - seconds_since_last_request ) )

#def get_call_stack_strs(clip_most_recent=0, include_only_paths_starting_with=None):
#	import inspect, os, sys
#	parts = []
#	last_part = ""
#	ellipsis = "..."
#	case_sensitive_paths = (sys.platform != "win32")
#	if not case_sensitive_paths:
#		include_only_paths_starting_with = include_only_paths_starting_with.lower()
#	include_only_paths_starting_with = include_only_paths_starting_with.replace("\\", "/")
#
#	for stack_frame in inspect.stack()[clip_most_recent:]:
#		frame,code_path,line_num,fn_name,code,code_idx = stack_frame # [pylint] allow unused variables : pylint:disable=W0612
#
#		code_abs_path = os.path.abspath(code_path)
#		if not case_sensitive_paths:
#			code_abs_path = code_abs_path.lower()
#		code_abs_path = code_abs_path.replace("\\", "/")
#
#		if code_abs_path.startswith(include_only_paths_starting_with):
#			code_filename = os.path.basename(code_path)
#			part = "%s:%d(%s)"%(code_filename,line_num,fn_name)
#		else:
#			part = ellipsis
#
#		if part != ellipsis or part != last_part:
#			parts.append(part)
#
#		last_part = part
#
#	return tuple(parts)
#

