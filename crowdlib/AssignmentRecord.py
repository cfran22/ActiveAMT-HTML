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

from crowdlib.utility import namedtuple

AssignmentRecord = namedtuple("AssignmentRecord", (
	"accept_time",
	"answer_records",
	"approval_time",
	"assignment_id",
	"assignment_status",
	"auto_approval_time",
	"hit_id",
	"rejection_time",
	"requester_feedback",
	"submit_time",
	"worker_id",
))
