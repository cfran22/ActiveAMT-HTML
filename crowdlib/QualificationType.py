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

class QualificationType(object):
	def __init__(self, id, creation_time, name, description, keywords, is_active, retry_delay, test_xml, test_duration,
			answer_key_xml, auto_granted, auto_granted_value):
		self._init_args = tuple((k,v) for (k,v) in locals().items() if k!="self") # must be first line of __init__
		from crowdlib.utility import is_string
		assert is_string(id) and len(id)>0
		self._id                 = id
		self._creation_time      = creation_time
		self._name               = name
		self._description        = description
		self._keywords           = keywords
		self._is_active          = is_active
		self._retry_delay        = retry_delay
		self._test_xml           = test_xml
		self._test_duration      = test_duration
		self._answer_key_xml     = answer_key_xml
		self._auto_granted       = auto_granted
		self._auto_granted_value = auto_granted_value

	def __repr__(self):
		return self.__class__.__name__ + "(" + ", ".join("%s=%s"%(k,v) for (k,v) in self._init_args) + ")"

	def __str__(self):
		return "QualificationType(id=%r, name=%r)"%(self._id, self._name)

	# [pylint] accessing seemingly private members : pylint:disable=W0212
	id                 = property(lambda self:self._id)
	creation_time      = property(lambda self:self._creation_time)
	name               = property(lambda self:self._name)
	description        = property(lambda self:self._description)
	keywords           = property(lambda self:self._keywords)
	is_active          = property(lambda self:self._is_active)
	retry_delay        = property(lambda self:self._retry_delay)
	test_xml           = property(lambda self:self._test_xml)
	test_duration      = property(lambda self:self._test_duration)
	answer_key_xml     = property(lambda self:self._answer_key_xml)
	auto_granted       = property(lambda self:self._auto_granted)
	auto_granted_value = property(lambda self:self._auto_granted_value)
	# [pylint] accessing seemingly private members : pylint:enable=W0212

	@property
	def is_requestable(self):
		return True
		# IsRequestable (is_requestable) should be True for any qualification requirement that I created.
		#
		# "Specifies whether the Qualification type is one that a user can request through the
		#  Amazon Mechanical Turk web site, such as by taking a Qualification test. This value is
		#  false for Qualifications assigned automatically by the system."
		#
		# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationTypeDataStructureArticle.html

	def create_requirement(self, comparator, value, for_preview=False):
		# Comparator should be one of:  =, <, >, >=, <=, !=
		# Value should be an integer.
		from crowdlib.QualificationRequirement import QualificationRequirement
		return QualificationRequirement.integer_qualification_requirement(self._id, comparator, value, for_preview)