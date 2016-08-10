# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: January 2010
'''

from __future__ import division

__version__   = "0.8.46"
__author__    = "Alexander J. Quinn"
__license__   = "MIT License"
__copyright__ = "Copyright 2011, Alexander J. Quinn"

################################################################################
# COMPATIBILITY CHECK
#
# Check for a couple common installation issues:
# - wrong Python version (need >=2.6)
# - broken sqlite3 module (common problem with Redhat 4)
#
MINIMUM_PYTHON_VERSION = "2.5"
import sys
if sys.version[:3] < MINIMUM_PYTHON_VERSION:
	sys.stderr.write("\n")
	sys.stderr.write("**********************************************\n")
	sys.stderr.write("*  CrowdLib currently requires Python %s+   *\n"%MINIMUM_PYTHON_VERSION)
	sys.stderr.write("**********************************************\n")
	sys.stderr.write("\n")
	raise Exception("CrowdLib currently requires Python %s+"%MINIMUM_PYTHON_VERSION)

try:
	import sqlite3
	del sqlite3
except ImportError:
	sys.stderr.write("\n")
	sys.stderr.write("\n")
	sys.stderr.write("**********************************************\n")
	sys.stderr.write("*  Your Python install is broken.            *\n")
	sys.stderr.write("*                                            *\n")
	sys.stderr.write("*  When Python was compiled on this machine, *\n")
	sys.stderr.write("*  the SQLite3 libraries were not present or *\n")
	sys.stderr.write("*  not found.                                *\n")
	sys.stderr.write("**********************************************\n")
	sys.stderr.write("\n")
	sys.stderr.write("\n")
	raise
del sys


# [pylint] tolerate use of `id` (name of a built-in function) below : pylint:disable=W0622

# Private imports we want to keep out of the general crowdlib namespace.
#
# This is a hack.  Basically, if somebody does ...
#        import crowdlib
#        print(dir(crowdlib))
# ... I don't want them to see classes and things that aren't meant to be used
# directly by clients.  With this, there will be a single entry called "_".
class _(object):
	from crowdlib.AMT import AMT
	from crowdlib.AMTInstanceManager import AMTInstanceManager
	from crowdlib.CrowdLibSettings import CrowdLibSettings
	from crowdlib.RequesterStatistics import RequesterStatistics
	from crowdlib.QualificationRequirement import QualificationRequirement
	from crowdlib.QuestionField import TextField
	from crowdlib.QuestionField import NumberField
	from crowdlib.QuestionField import RadioButtonField
	from crowdlib.QuestionField import MultiChooserField
	from crowdlib.QuestionField import DropDownField
	from crowdlib.QuestionField import ComboBoxField
	from crowdlib.QuestionField import CheckBoxField
	from crowdlib.QuestionField import FileUploadField
	from crowdlib.QuestionField import ListField

	settings = CrowdLibSettings()   # CrowdLibSettings is a singleton class.

	amt_instance_manager = AMTInstanceManager()

	@staticmethod
	def get_amt():
		return _.amt_instance_manager.get_amt(_.settings)


################################################################################
# GLOBAL SETTINGS OBJECT
settings = _.settings



################################################################################
# CREATING HITS
#

def create_hit_type(title,
					description,
					reward=None,
					currency=None,
					time_limit=None,
					keywords=None,
					autopay_delay=None,
					qualification_requirements=None):
	# Passing None means to use your defaults from your settings.
	# Amazon does not allow "" for description.  You will get an error if you try.

	hit_type = _.get_amt().create_hit_type(
			title=title,
			description=description,
			reward=reward,
			currency=currency,
			time_limit=time_limit,
			keywords=keywords,
			autopay_delay=autopay_delay,
			qualification_requirements=qualification_requirements)
	return hit_type

def text_field(label, id):
	return _.TextField(label=label, id=id)

def checkbox_field(label, id, choices):
	return _.CheckBoxField(label, id, choices)

def combobox_field(label, id, choices):
	return _.ComboBoxField(label, id, choices)

def dropdown_field(label, id, choices):
	return _.DropDownField(label, id, choices)

def file_upload_field(label, id, min_bytes=0, max_bytes=2000000000):
	return _.FileUploadField(label, id, min_bytes, max_bytes)

def list_field(label, id, choices):
	return _.ListField(label, id, choices)

def multichooser_field(label, id, choices):
	return _.MultiChooserField(label, id, choices)

def number_field(label, id, min_value=None, max_value=None):
	return _.NumberField(label=label, id=id, min_value=min_value, max_value=max_value)

def radiobutton_field(label, id, choices, other=None):
	return _.RadioButtonField(label, id, choices, other)


################################################################################
# RECEIVING RESULTS
#

def get_current_notification_events(cgi_fields=None):
	return _.get_amt().get_current_notification_events_from_cgi(cgi_fields)

def start_notifications(url):
	return _.get_amt().start_notifications(url)

def stop_notifications():
	return _.get_amt().stop_notifications()

################################################################################
# GETTERS
#

def get_hit_type(id):
	from crowdlib.utility import to_unicode
	hit_type_id = to_unicode(id)
	return _.get_amt().get_hit_type(hit_type_id, do_sync_if_not_found=True)

def get_hit_types(since=None, until=None, title_re=None):
	from crowdlib.utility import coerce_to_date_time
	from crowdlib.utility.miscellaneous import GeneratingSequence
	since = coerce_to_date_time(since, interpret_durations_as_past=True, default_time="00:00:00.000000")
	until = coerce_to_date_time(until, interpret_durations_as_past=True, default_time="23:59:59.999999")
	return GeneratingSequence(_.get_amt().get_hit_types(since=since, until=until, title_re=title_re))

def get_hit(id):
	from crowdlib.utility import to_unicode
	hit_id = to_unicode(id)
	return _.get_amt().get_hit(hit_id)

def get_hits(since=None, until=None, title_re=None):
	from crowdlib.utility import coerce_to_date_time
	from crowdlib.utility.miscellaneous import GeneratingSequence
	since = coerce_to_date_time(since, interpret_durations_as_past=True, default_time="00:00:00.000000")
	until = coerce_to_date_time(until, interpret_durations_as_past=True, default_time="23:59:59.999999")
	return GeneratingSequence(_.get_amt().get_hits(since=since, until=until, title_re=title_re))

def get_qualification_types():
	from crowdlib.utility.miscellaneous import GeneratingSequence
	return GeneratingSequence(_.get_amt().get_qualification_types())

def get_qualification_type(id):
	from crowdlib.utility import to_unicode
	qualification_type_id = to_unicode(id)
	return _.get_amt().get_qualification_type(qualification_type_id)

def get_worker(id):
	from crowdlib.utility import to_unicode
	worker_id = to_unicode(id)
	return _.get_amt().get_worker(worker_id)

def get_workers(since=None, until=None, title_re=None):
	from crowdlib.utility import coerce_to_date_time
	from crowdlib.utility.miscellaneous import GeneratingSequence
	since = coerce_to_date_time(since, interpret_durations_as_past=True, default_time="00:00:00.000000")
	until = coerce_to_date_time(until, interpret_durations_as_past=True, default_time="23:59:59.999999")
	return GeneratingSequence(_.get_amt().get_workers(since=since, until=until, title_re=title_re))

def get_assignment(id):
	from crowdlib.utility import to_unicode
	assignment_id = to_unicode(id)
	return _.get_amt().get_assignment(assignment_id)

def get_assignments(since=None, until=None, title_re=None):
	from crowdlib.utility import coerce_to_date_time
	from crowdlib.utility.miscellaneous import GeneratingSequence
	since = coerce_to_date_time(since, interpret_durations_as_past=True, default_time="00:00:00.000000")
	until = coerce_to_date_time(until, interpret_durations_as_past=True, default_time="23:59:59.999999")
	return GeneratingSequence(_.get_amt().get_assignments(since=since, until=until, title_re=title_re))

def get_account_balance():
	return _.get_amt().get_account_balance()


################################################################################
# HOUSEKEEPING
#

def sync_with_amt():
	_.get_amt().sync_with_amt()

def set_all_hits_unavailable():
	_.get_amt().set_all_hits_unavailable()

requester_statistics        = _.RequesterStatistics(_.get_amt, time_period="LifeToDate")
requester_statistics_by_day = _.RequesterStatistics(_.get_amt, time_period="OneDay")


################################################################################
# QUALIFICATION REQUIREMENTS
#

def create_agreement_requirement(name, description, xhtml, agree_text, keywords=None, initially_active=True, for_preview=False):
	return _.get_amt().create_click_through_qualification_requirement(name=name,
			description=description, xhtml=xhtml, agree_text=agree_text, keywords=keywords,
			initially_active=initially_active, required_to_preview=for_preview)

def create_qualification_type( name, description, initially_active=None,
							   keywords=None, retry_delay=None,
							   test_xml=None, answer_key_xml=None,
							   test_duration=None, auto_granted=None, auto_granted_value=None,
							   is_requestable=None):
	if initially_active is None:
		initially_active = True
	if keywords is None:
		keywords = ()
	# retry_delay may be None  (to indicate that retry is not allowed)
	# test_xml may be None (to indicate that the worker need not do a test)
	# answer_key_xml may be None (to indicate that you will process requests manually)
	# test_duration may be None but only if test_xml is None
	if auto_granted is None:
		auto_granted = False
	# auto_granted_value may be None but only if auto_granted==False and must not be None otherwise.
	qualification_type = _.get_amt().create_qualification_type(name=name, description=description, initially_active=initially_active,
								   keywords=keywords, retry_delay=retry_delay,
								   test_xml=test_xml, answer_key_xml=answer_key_xml,
								   test_duration=test_duration, auto_granted=auto_granted, auto_granted_value=auto_granted_value,
								   is_requestable=is_requestable)
	return qualification_type

################################################################################
# BUILT-IN QUALIFICATION REQUIREMENTS
#

def masters_requirement(for_preview=False):  # min_pct between 0 and 100
	return _.QualificationRequirement.masters_qualification_requirement(_.settings.service_type, for_preview)

def photo_moderation_masters_requirement(for_preview=False):  # min_pct between 0 and 100
	return _.QualificationRequirement.photo_moderation_masters_qualification_requirement(_.settings.service_type, for_preview)

def categorization_masters_requirement(for_preview=False):  # min_pct between 0 and 100
	return _.QualificationRequirement.categorization_masters_qualification_requirement(_.settings.service_type, for_preview)

def approval_requirement(min_pct, for_preview=False):  # min_pct between 0 and 100
	return _.QualificationRequirement.approval_rate_qualification_requirement(min_pct, for_preview)

def submission_requirement(min_pct, for_preview=False):  # min_pct between 0 and 100
	return _.QualificationRequirement.submission_rate_qualification_requirement(min_pct, for_preview)

def return_requirement(max_pct, for_preview=False):  # max_pct between 0 and 100
	return _.QualificationRequirement.return_rate_qualification_requirement(max_pct, for_preview)

def abandon_requirement(max_pct, for_preview=False):  # max_pct between 0 and 100
	return _.QualificationRequirement.abandon_rate_qualification_requirement(max_pct, for_preview)

def rejection_requirement(max_pct, for_preview=False):  # max_pct between 0 and 100
	return _.QualificationRequirement.rejection_rate_qualification_requirement(max_pct, for_preview)

def adult_requirement(for_preview=False):
	return _.QualificationRequirement.adult_qualification_requirement(for_preview)

def in_country_requirement(country, for_preview=False):
	# country is a ISO 3166 a code (e.g. US, IN, PK, CN, MX, CA, etc.)
	return _.QualificationRequirement.locale_qualification_requirement("EqualTo", country, for_preview)

def not_in_country_requirement(country, for_preview=False):
	# country is a ISO 3166 a code (e.g. US, IN, PK, CN, MX, CA, etc.)
	return _.QualificationRequirement.locale_qualification_requirement("NotEqualTo", country, for_preview)



################################################################################
# UTILITY
#

from crowdlib.utility import to_duration
from crowdlib.utility import to_date_time as to_datetime
from crowdlib.utility import to_date

from crowdlib.reports import assignment_report


################################################################################
# EXCEPTIONS
#

from crowdlib.all_exceptions import AssignmentAlreadyFinalizedException
from crowdlib.all_exceptions import HITNotFoundException
from crowdlib.all_exceptions import HITTypeNotFoundException
from crowdlib.all_exceptions import AssignmentNotFoundException
from crowdlib.all_exceptions import WorkerNotFoundException
from crowdlib.all_exceptions import CannotInterpretDateTimeError
from crowdlib.all_exceptions import CannotInterpretDurationError
from crowdlib.all_exceptions import AMTRequestFailed





# Clean up the namespace
del division


if __name__=="__main__":
	print( "\nThis is just a module, not the code entry point.\n" )
