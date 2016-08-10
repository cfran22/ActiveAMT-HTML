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

QualificationRequirementRecord = namedtuple("QualificationRequirementRecord", (
	"qualification_type_id",
	"comparator",
	"integer_value",
	"locale_value",
	"required_to_preview")
)
