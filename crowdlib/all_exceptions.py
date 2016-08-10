# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: October 2010 (approx)
'''

from __future__ import division, with_statement

class CrowdLibBaseException(Exception):
	def __str__( self ):
		from crowdlib.utility import is_sequence_of_strings, to_tuple_if_non_sequence_iterable
		args = self.args
		args = to_tuple_if_non_sequence_iterable(args)
		if is_sequence_of_strings(args) and len(args)==1:
			return args[0]
		else:
			return repr(args)
	
	@property
	def message(self):
		return str(self)

	__repr__=__str__


class AMTRequestFailed( CrowdLibBaseException ): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
	'''
	Exception indicating some problem with the query to AMT.
	'''
	def __init__( self, code, msg, operation, query_params=None ): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
		self.code = code
		self.msg = msg
		self.operation = operation
		self.query_params = query_params

	def _param_str(self):
		return repr(tuple(sorted(self.__dict__)))
	def __str__( self ):
		return "%s during %s: %s"%(self.code, self.operation, self.msg)
	def __repr__( self ):
		return "AMTRequestFailed( %s, %s, %s )"%( self.code, self.msg, self.operation )


class AMTNotificationNotAvailable(CrowdLibBaseException):
	pass

class NotificationsAddressNotFoundException(CrowdLibBaseException):
	def __init__(self, hit_type_id): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
		self.hit_type_id = hit_type_id

class AMTQualificationTypeAlreadyExists(AMTRequestFailed):
	def __init__(self, code, msg, operation, name):
		AMTRequestFailed.__init__(self, code, msg, operation)
		self.name = name

	def __str__( self ):
		return "A QualificationType with the name %r already exists. ... Try changing a character in the name.  Notify Alex Quinn if this persists."%self.name

	def __repr__( self ):
		return "AMTQualificationTypeAlreadyExists(%s, %s, %s, %s )"% \
							( self.code, self.msg, self.operation, self.name )


class AssignmentAlreadyFinalizedException(CrowdLibBaseException):
	def __init__(self, assignment_id, assignment_status): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
		self.assignment_id = assignment_id
		self.assignment_status = assignment_status

	@property
	def message(self):
		return "Already %s"%(self.assignment_status.lower())

	def __str__(self):
		return "AssignmentAlreadyFinalizedException(%s, %s)"%(self.assignment_id, self.assignment_status)
	__repr__ = __str__


class NotFoundException(CrowdLibBaseException):
	pass


class AssignmentNotFoundException(NotFoundException):
	def __init__(self, assignment_id, msg=""):
		NotFoundException.__init__(self, assignment_id, msg)
		self.assignment_id = assignment_id
		if msg=="":
			msg = assignment_id
		elif assignment_id not in msg:
			msg = msg + "(" + assignment_id + ")"
		self.msg = msg


class HITTypeNotFoundException(NotFoundException):
	def __init__(self, hit_type_id, msg=""):
		NotFoundException.__init__(self, hit_type_id, msg)
		self.hit_type_id = hit_type_id
		if msg=="":
			msg = hit_type_id
		elif hit_type_id not in msg:
			msg = msg + "(" + hit_type_id + ")"
		self.msg = msg


class HITNotFoundException(NotFoundException):
	def __init__(self, hit_id, msg=""):
		NotFoundException.__init__(self, hit_id, msg)
		self.hit_id = hit_id
		if msg=="":
			msg = hit_id
		elif hit_id not in msg:
			msg = msg + "(" + hit_id + ")"
		self.msg = msg

class QualificationTypeNotFoundException(NotFoundException):
	def __init__(self, qtype_id, msg=""):
		NotFoundException.__init__(self, qtype_id, msg)
		self.qualification_type_id = qtype_id
		if msg=="":
			msg = qtype_id
		elif qtype_id not in msg:
			msg = msg + "(" + qtype_id + ")"
		self.msg = msg

class WorkerNotFoundException(NotFoundException):
	def __init__(self, worker_id, msg=""):
		NotFoundException.__init__(self, worker_id, msg)
		self.worker_id = worker_id
		if msg=="":
			msg = worker_id
		elif worker_id not in msg:
			msg = msg + "(" + worker_id + ")"
		self.msg = msg

class CannotInterpretError(ValueError, CrowdLibBaseException):
	pass

class CannotInterpretDurationError(CannotInterpretError):
	pass

class CannotInterpretDateTimeError(CannotInterpretError):
	pass

class CannotInterpretDateError(CannotInterpretError):
	pass

class CannotInterpretTimeError(CannotInterpretError):
	pass

class QuestionXMLError(CrowdLibBaseException):
	def __init__(self, xml_str, amt_error_msg, amt_error_code): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
		self.xml = xml_str
		self.amt_error_code = amt_error_code
		self.amt_error_msg  = amt_error_msg

		from crowdlib.utility import xml2dom
		import xml.parsers.expat

		try:
			xml2dom(xml_str)
			self.msg = "Question XML appears to be well-formed XML.  However, it was not accepted by the Amazon Mechanical Turk server.  This probably means it conform to neither the QuestionForm or the ExternalQuestion schemas.  AWS said: %s, %s"%(amt_error_code, amt_error_msg)
			self.is_well_formed = True
		except xml.parsers.expat.ExpatError:
			import sys
			e = sys.exc_info()[1]
			self.is_well_formed = False
			emsg = e.message
			emsg = emsg[0].upper() + emsg[1:]
			self.msg = "Question XML is not well-formed XML.  " + emsg

	def __str__(self):
		return self.msg

class CrowdLibInternalError(CrowdLibBaseException):
	def __init__( self, msg ): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
		self.msg = msg

	def __str__(self):
		return self.msg

class AMTDataError(CrowdLibInternalError):
	pass

class XMLProcessingException(CrowdLibInternalError):
	def __init__( self, msg ): # [pylint] doesn't call super(..).__init__(..) : pylint:disable=W0231
		self.msg = msg

	def __str__(self):
		return self.msg

class CrowdLibSettingsError(ValueError):
	pass





#JUNK#class AMTConnectionNotOpenException(CrowdLibBaseException):
#JUNK#	pass

#JUNK#class CannotUpdateAssignmentException(CrowdLibBaseException):
#JUNK#	pass

#JUNK#class CaughtKeyboardInterrupt(KeyboardInterrupt):
#JUNK#	pass

#JUNK#class AbstractClassMethodException( CrowdLibBaseException ):
#JUNK#	pass

#JUNK#class CrowdLibNotEnabledException(CrowdLibBaseException):
#JUNK#	pass

# [no longer used as far as I know, 12/4/2013]
#class CrowdLibOperationException(Exception):
#	msg = ""
#
#	def __str__( self ):
#		return "%s during %s: %s"%(self.code, self.operation, self.msg)
#
#	def __repr__( self ):
#		type_name = type(self).__name__
#		param_str = ", ".join((k+"="+repr(v)) for (k,v) in self.__dict__.items())
#		return type_name + "(" + param_str + ")"

#	def print_msg( self ):
#		from crowdlib.utility import log
#		log( '- Error:  '+', '.join( (self.code, self.msg, self.operation) ) )

#	def print_msg( self ):
#		from crowdlib.utility import log
#		log(str(self))

#class HITNotFoundException(NotFoundException):
#	def __init__(self, hit_id, msg=""):
#		self.hit_id = hit_id
#		self.msg = msg


