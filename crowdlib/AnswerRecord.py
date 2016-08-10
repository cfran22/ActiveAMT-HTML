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

AnswerRecord = namedtuple("AnswerRecord", (
#		 "assignment_id",
		 "question_identifier", "free_text", "selection_identifier", "other_selection",
		 "uploaded_file_key", "uploaded_file_size_in_bytes"))
