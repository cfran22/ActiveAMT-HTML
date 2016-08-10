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

# INTERNAL USE ONLY - NOT RETURNED TO THE USER OF THE CROWDLIB MODULE

from utility import namedtuple

HITRecord = namedtuple("HITRecord", (
		"assignment_duration",
		"auto_approval_delay",
		"creation_time",
		"description",
		"expiration_time",
		"hit_id",
		"hit_review_status",          # by default, would come only with GetHITs
		"hit_status",
		"hit_type_id",
		"keywords",
		"max_assignments",
		"num_available",              # by default, would come only with SearchHITs
		"num_completed",              # by default, would come only with SearchHITs
		"num_pending",                # by default, would come only with SearchHITs
		"number_of_similar_hits",     # by default, would come only with GetHITs
		"qualification_requirements", # by default, would come only with GetHITs
		"question",                   # by default, would come only with GetHITs
		"requester_annotation",
		"reward",
		"title",
))

HITRecordDB = namedtuple("HITRecordDB", (
		"creation_time",
		"expiration_time",
		"hit_id",
		"hit_review_status",
		"hit_status",
		"hit_type_id",
		"max_assignments",
		"num_available",
		"num_completed",
		"num_pending",
		"question",
		"requester_annotation",
		"approximate_expiration_time",
))

HITTypeRecord = namedtuple("HITTypeRecord", (
		"assignment_duration",
		"auto_approval_delay",
		"description",
		"hit_type_id",
		"keywords",
		"reward",
		"title"
))

HITTypeRecordDB = namedtuple("HITTypeRecordDB", (
		"assignment_duration",
		"auto_approval_delay",
		"description",
		"hit_type_id",
		"keywords",
		"qualification_requirements",
		"reward",
		"title"
))
