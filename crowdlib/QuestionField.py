# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: December 2010
'''

from __future__ import division, with_statement

# TODO:  Support DefaultText, NumberOfLinesSuggestion, IsNumeric, Length, AnswerFormatRegex (incl. regex, errorText, flags)
#                Binary (i.e., images), Java applets, Flash applications

class AbstractQuestionField(object):
	def __init__(self, label, id):
		self._label = label
		self._id = id

	def _make_question_xml(self, answer_spec):
		from xml.sax.saxutils import escape
		from crowdlib.utility.type_utils import to_unicode
		question_content_xml = make_text_or_formatted_content_xml(self._label)
		xml = '''\
		  <Question>
			<QuestionIdentifier>%(id)s</QuestionIdentifier>
			<QuestionContent>
			  %(question_content_xml)s
			</QuestionContent>
			<AnswerSpecification>
			%(answer_spec)s
			</AnswerSpecification>
		  </Question>
		'''%{
				"question_content_xml" : question_content_xml,
				"id"    : escape(to_unicode(self._id)),
				"answer_spec" : answer_spec
		}
		return xml

class FileUploadField(AbstractQuestionField):
	def __init__(self, label, id, min_bytes, max_bytes):
		super(FileUploadField,self).__init__(label, id)
		self._min_bytes = min_bytes
		self._max_bytes = max_bytes

	@property
	def xml(self):
		answer_spec = "<FileUploadAnswer>" + \
				  "<MaxFileSizeInBytes>%d</MaxFileSizeInBytes>"%self._max_bytes + \
				  "<MinFileSizeInBytes>%d</MinFileSizeInBytes>"%self._min_bytes + \
			  "</FileUploadAnswer>"
		xml = self._make_question_xml(answer_spec)
		return xml

class AbstractTextField(AbstractQuestionField):
	def __init__(self, label, id):
		super(AbstractTextField,self).__init__(label, id)
		self._freetext_answer_content = ""

	def _make_freetext_answer_spec(self, freetext_answer_content=None):
		if freetext_answer_content is None:
			freetext_answer_content = ""
		xml = "<FreeTextAnswer>" + freetext_answer_content + "</FreeTextAnswer>"
		return xml

	@property
	def xml(self):
		answer_spec = self._make_freetext_answer_spec()
		xml = self._make_question_xml(answer_spec)
		return xml

class TextField(AbstractTextField):
	pass

class NumberField(TextField):
	def __init__(self, label, id, min_value=None, max_value=None):
		super(NumberField,self).__init__(label, id)
		self._min_value = min_value
		self._max_value = max_value

	@property
	def xml(self):
		min_value_str = ((' minValue="%s"'%self._min_value) if (self._min_value is not None) else "")
		max_value_str = ((' maxValue="%s"'%self._max_value) if (self._max_value is not None) else "")
		freetext_answer_content = "<Constraints><IsNumeric%s%s /></Constraints>"%(min_value_str, max_value_str)
		answer_spec = self._make_freetext_answer_spec(freetext_answer_content=freetext_answer_content)
		xml = self._make_question_xml(answer_spec)
		return xml

class AbstractSelectionField(AbstractQuestionField):
	_style_suggestion = None
	def __init__(self, label, id, choices, other=None, min_selection_count=None, max_selection_count=None):
		super(AbstractSelectionField,self).__init__(label, id)
		if max_selection_count is None:
			max_selection_count = len(choices)
			if other is not None:
				max_selection_count += 1
		self._max_selection_count = max_selection_count
		self._min_selection_count = min_selection_count
		self._other = other
		self._choices = choices

	@property
	def xml(self):
		from xml.sax.saxutils import escape
		from crowdlib.utility.type_utils import to_unicode
		assert self._style_suggestion is not None, repr(self)
		answer_spec_lines = []
		answer_spec_lines.append("<SelectionAnswer>")
		if self._min_selection_count is not None:
			answer_spec_lines.append("<MinSelectionCount>%s</MinSelectionCount>"%self._min_selection_count)
		if self._max_selection_count is not None:
			answer_spec_lines.append("<MaxSelectionCount>%s</MaxSelectionCount>"%self._max_selection_count)
		answer_spec_lines.append("<StyleSuggestion>%s</StyleSuggestion>"%self._style_suggestion)
		answer_spec_lines.append("<Selections>")
		i = -1
		for choice in self._choices:
			i += 1
			answer_spec_lines.append("<Selection>")
			answer_spec_lines.append("<SelectionIdentifier>%s</SelectionIdentifier>"%(escape(to_unicode(i))))
			answer_spec_lines.append(make_text_or_formatted_content_xml(choice))
			answer_spec_lines.append("</Selection>")

		if self._other:
			if not isinstance(self._other, AbstractTextField):
				raise TypeError("other must be a text field")

			other_xml = self._other.xml
			assert other_xml.startswith("<FreeTextAnswer>")
			assert other_xml.endswith("</FreeTextAnswer>")

			other_xml = other_xml[len("<FreeTextAnswer>"):-len("</FreeTextAnswer>")]
			answer_spec_lines.append("<OtherSelection>")
			answer_spec_lines.append(other_xml)
			answer_spec_lines.append("</OtherSelection>")

		answer_spec_lines.append("</Selections>")
		answer_spec_lines.append("</SelectionAnswer>")
		answer_spec = "".join(answer_spec_lines)
		xml = self._make_question_xml(answer_spec)
		return xml

class RadioButtonField(AbstractSelectionField):
	_style_suggestion = "radiobutton"
	def __init__(self, label, id, choices, other=None):
		super(RadioButtonField,self).__init__(label, id, choices, min_selection_count=1, max_selection_count=1, other=other)

class CheckBoxField(AbstractSelectionField):
	_style_suggestion = "checkbox"

class ListField(AbstractSelectionField): # seems to be same as radio button!!!
	_style_suggestion = "list"

class DropDownField(AbstractSelectionField):
	_style_suggestion = "dropdown"
	def __init__(self, label, id, choices):
		super(DropDownField,self).__init__(label, id, choices, other=None, min_selection_count=1, max_selection_count=1)

class ComboBoxField(AbstractSelectionField):
	_style_suggestion = "combobox"

class MultiChooserField(AbstractSelectionField):  # seems to be same as check boxes!!!
	_style_suggestion = "multichooser"

def make_text_or_formatted_content_xml(content):
	from xml.sax.saxutils import escape
	from crowdlib.utility.xml_helpers import to_cdata, looks_like_limited_xhtml
	from crowdlib.utility.type_utils import is_string, to_unicode
	assert is_string(content)
	content = to_unicode(content)
	if looks_like_limited_xhtml(content):
		return "<FormattedContent>%s</FormattedContent>"%(to_cdata(content))
	else:
		return "<Text>%s</Text>"%(escape(content))
