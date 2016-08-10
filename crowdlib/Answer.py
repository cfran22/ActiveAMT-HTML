# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: January 2010
'''

from __future__ import division, with_statement

#TODO: Go back and figure out why AnswerBlank is needed.  This may be garbage.
#TODO: Cannonical representation for AnswerUploadedFile

ANSWER_TYPES = ANSWER_TYPE_BLANK,ANSWER_TYPE_FREETEXT,ANSWER_TYPE_SELECTION,ANSWER_TYPE_UPLOADEDFILE \
		     = ("Blank", "FreeText", "Selection", "UploadedFile")

class Answer( object ):
	"Abstract base class for AnswerFreeText, AnswerSelection, AnswerUploadedFile"

	def __init__( self, question_id, answer_type, assignment_id, amt):
		assert answer_type in ANSWER_TYPES
		self._question_id = question_id
		self._answer_type = answer_type
		self._assignment_id = assignment_id
		self._amt = amt # needed for fetching the assignment or downloading file contents in the case of UploadedFile
	
	# [pylint] accessing seemingly private members : pylint:disable=W0212
	question_id = property(lambda self: self._question_id)
	answer_type = property(lambda self: self._answer_type)
	assignment = property(lambda self: self._amt.get_assignment(self._assignment_id))
	# [pylint] accessing seemingly private members : pylint:enable=W0212

	def __eq__( self, other ):
		return type(other)==type(self) and repr(self)==repr(other)
	
	def __ne__( self, other ):
		return not self.__eq__(other)

	def __str__( self ):
		raise NotImplementedError( "cannonical_representation of %s"%repr(self) )

	@property
	def text(self):
		return unicode(self)

	@property
	def id(self):
		return self._assignment_id + "-" + self._question_id

class AnswerBlank( Answer ):
	'''
	For dealing with Assignment structures where there is no legitimate answer
	present.
	'''

	def __init__( self, question_id, assignment_id, amt ):
		Answer.__init__(self, question_id, ANSWER_TYPE_BLANK, assignment_id, amt)

	def __repr__(self):
		return ANSWER_TYPE_BLANK+repr( ( self.question_id, ) )

	def __str__( self ):
		return ""

class AnswerFreeText( Answer ):
	def __init__( self, question_id, free_text, assignment_id, amt):
		Answer.__init__(self, question_id, ANSWER_TYPE_FREETEXT, assignment_id, amt)
		self._free_text = free_text

	free_text = property(lambda self: self._free_text) # [pylint] accessing seemingly private members : pylint:disable=W0212

	def __repr__(self):
		return "AnswerFreeText"+repr( ( self.question_id, self.free_text ) )

	def __str__( self ):
		return self.free_text

class AnswerSelection( Answer ):
	def __init__( self, question_id, selection_id, other_selection_text, assignment_id, amt):
		Answer.__init__(self, question_id, ANSWER_TYPE_SELECTION, assignment_id, amt)
		self._selection_id = selection_id
		self._other_selection_text = other_selection_text

	# [pylint] accessing seemingly private members : pylint:disable=W0212
	selection_id = property(lambda self: self._selection_id)
	other_selection_text = property(lambda self: self._other_selection_text)
	# [pylint] accessing seemingly private members : pylint:enable=W0212

	def __repr__(self):
		return "AnswerSelection"+repr( ( self.question_id, self.selection_id, self.other_selection_text ) )

	def __str__( self ):
		return self.selection_id

class AnswerUploadedFile( Answer ):
	def __init__( self, question_id, uploaded_file_key, uploaded_file_size, assignment_id, amt):
		Answer.__init__(self, question_id, ANSWER_TYPE_UPLOADEDFILE, assignment_id, amt)
		self._uploaded_file_key = uploaded_file_key
		self._uploaded_file_size = uploaded_file_size

	# [pylint] accessing seemingly private members : pylint:disable=W0212
	key = property(lambda self: self._uploaded_file_key)
	size = property(lambda self: self._uploaded_file_size)
	# [pylint] accessing seemingly private members : pylint:enable=W0212
	
	def save(self, path):
		self._amt.save_file_answer_content(assignment_id=self._assignment_id, question_id=self._question_id, path=path)
	
	@property
	def content(self):
		return self._amt.get_file_answer_content(assignment_id=self._assignment_id, question_id=self._question_id)

	def __repr__(self):
		return "AnswerUploadedFile"+repr( ( self._question_id, self._uploaded_file_key, self._uploaded_file_size ) )

	def __str__(self):
		return repr(self)