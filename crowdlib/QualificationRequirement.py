# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: June 2010
'''

from __future__ import division, with_statement

# FIXME:  Add comparator "Exists". http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/index.html?ApiReference_OperationsArticle.html

class QualificationRequirement( object ):
	# A requirement imposed on workers before they can work on the HIT.
    # 
	# This must be registered with the server in order to get the qualification_type_id.
	# Some common qualifications are already registered by Amazon.

	VALID_COMPARATORS = ("=", "<", ">", ">=", "<=", "!=", "EqualTo", "LessThan", "GreaterThan", "GreaterThanOrEqualTo", "LessThanOrEqualTo", "NotEqualTo", "Exists")

	def __init__(self, qualification_type_id, comparator, integer_value, locale_value, required_to_preview):
		if comparator not in self.VALID_COMPARATORS:
			raise ValueError("Unexpected comparator: "+repr(comparator))
		self._qualification_type_id = qualification_type_id
		self._comparator = self._expand_comparator(comparator)
		self._comparator_short = self._shorten_comparator(comparator)
		self._integer_value = integer_value
		self._locale_value = locale_value
		self._required_to_preview = required_to_preview
	
	qualification_type_id = property(lambda self: self._qualification_type_id) # [pylint] access protected member : pylint:disable=W0212
	comparator = property(lambda self: self._comparator)                       # [pylint] access protected member : pylint:disable=W0212
	integer_value = property(lambda self: self._integer_value)                 # [pylint] access protected member : pylint:disable=W0212
	locale_value = property(lambda self: self._locale_value)                   # [pylint] access protected member : pylint:disable=W0212
	required_to_preview = property(lambda self: self._required_to_preview)     # [pylint] access protected member : pylint:disable=W0212

	def __repr__(self):
		return "QualificationRequirement" + repr((self.qualification_type_id,self.comparator,self.integer_value))
	
	__str__ = __repr__

	@classmethod
	def masters_qualification_requirement(cls, service_type, required_to_preview):
		if service_type == "sandbox":
			qualification_type_id = "2ARFPLSP75KLA8M8DH1HTEQVJT3SY6"
		elif service_type == "production":
			qualification_type_id = "2F1QJWKUDD8XADTFD2Q0G6UTO95ALH"
		return cls(qualification_type_id=qualification_type_id, comparator="Exists",
				integer_value=None, locale_value=None, required_to_preview=required_to_preview)

	@classmethod
	def categorization_masters_qualification_requirement(cls, service_type, required_to_preview):
		if service_type == "sandbox":
			qualification_type_id = "2F1KVCNHMVHV8E9PBUB2A4J79LU20F"
		elif service_type == "production":
			qualification_type_id = "2NDP2L92HECWY8NS8H3CK0CP5L9GHO"
		return cls(qualification_type_id=qualification_type_id, comparator="Exists",
				integer_value=None, locale_value=None, required_to_preview=required_to_preview)

	@classmethod
	def photo_moderation_masters_qualification_requirement(cls, service_type, required_to_preview):
		if service_type == "sandbox":
			qualification_type_id = "2TGBB6BFMFFOM08IBMAFGGESC1UWJX"
		elif service_type == "production":
			qualification_type_id = "21VZU98JHSTLZ5BPP4A9NOBJEK3DPG"
		return cls(qualification_type_id=qualification_type_id, comparator="Exists",
				integer_value=None, locale_value=None, required_to_preview=required_to_preview)

	@classmethod
	def return_rate_qualification_requirement(cls, max_value, required_to_preview):
		qualification_type_id = "000000000000000000E0"
		comparator = "<"
		return cls(qualification_type_id, comparator, max_value, None, required_to_preview)

	@classmethod
	def abandon_rate_qualification_requirement(cls, max_value, required_to_preview):
		# Deprecated? ... No longer listed in the API documentation.
		# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
		qualification_type_id = "00000000000000000070"
		comparator = "<"
		return cls(qualification_type_id, comparator, max_value, None, required_to_preview)

	@classmethod
	def rejection_rate_qualification_requirement(cls, max_value, required_to_preview):
		# Deprecated? ... No longer listed in the API documentation.
		# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
		qualification_type_id = "000000000000000000S0"
		comparator = "<"
		return cls(qualification_type_id, comparator, max_value, None, required_to_preview)

	@classmethod
	def approval_rate_qualification_requirement(cls, min_value, required_to_preview):
		qualification_type_id = "000000000000000000L0"
		comparator = ">"
		return cls(qualification_type_id, comparator, min_value, None, required_to_preview)

	@classmethod
	def submission_rate_qualification_requirement(cls, min_value, required_to_preview):
		# Deprecated? ... No longer listed in the API documentation.
		# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
		qualification_type_id = "00000000000000000000"
		# Yes, it really is all zeros.
		# http://docs.amazonwebservices.com/AWSMechanicalTurkRequester/2007-06-21/ApiReference_QualificationRequirementDataStructureArticle.html
		comparator = ">"
		return cls(qualification_type_id, comparator, min_value, None, required_to_preview)

	@classmethod
	def adult_qualification_requirement(cls, required_to_preview):
		qualification_type_id = "00000000000000000060"
		comparator = "="
		integer_value = 1
		return cls(qualification_type_id, comparator, integer_value, None, required_to_preview)

	@classmethod
	def integer_qualification_requirement(cls, qualification_type_id, comparator, integer_value, required_to_preview):
		return cls(qualification_type_id, comparator, integer_value, None, required_to_preview)

	@classmethod
	def locale_qualification_requirement(cls, comparator, country_code_iso_3166, required_to_preview):
		# Example country codes:
		#  - Canada: CA
		#  - China: CN
		#  - India:  IN
		#  - Mexico: MX
		#  - Pakistan: PK
		#  - United States: US
		if comparator not in ("!=", "=", "NotEqualTo", "EqualTo"):
			raise ValueError("Unexpected comparator for LocaleQualificationRequirement: "+repr(comparator))
		qualification_type_id = "00000000000000000071"
		return cls(qualification_type_id, comparator, None, country_code_iso_3166, required_to_preview)

	def _shorten_comparator(self,comparator):
		# Convert "Equals" to "=" and so forth.  If the short version is passed in, just return it unchanged.
		# This is the inverse of _expand_comparator(..).
		assert comparator in self.VALID_COMPARATORS
		if comparator=="EqualTo":
			comparator = "="
		elif comparator=="LessThan":
			comparator = "<"
		elif comparator == "LessThanOrEqualTo":
			comparator = "<="
		elif comparator == "GreaterThan":
			comparator = ">"
		elif comparator == "GreaterThanOrEqualTo":
			comparator = ">="
		elif comparator == "NotEqualTo":
			comparator = "!="
		assert comparator in self.VALID_COMPARATORS
		return comparator

	def _expand_comparator(self,comparator):
		# Convert "=" to "EqualTo" and so forth.  If the short version is passed in, just return it unchanged.
		# This is the inverse of _shorten_comparator(..).
		assert comparator in self.VALID_COMPARATORS
		if comparator=="=":
			comparator = "EqualTo"
		elif comparator=="<":
			comparator = "LessThan"
		elif comparator == "<=":
			comparator = "LessThanOrEqualTo"
		elif comparator == ">":
			comparator = "GreaterThan"
		elif comparator == ">=":
			comparator = "GreaterThanOrEqualTo"
		elif comparator == "!=":
			comparator = "NotEqualTo"
		assert comparator in self.VALID_COMPARATORS
		return comparator
