# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alex Quinn
@contact: aq@cs.umd.edu
@since: January 2010
'''

from __future__ import division, with_statement

class Table(object):
	
	def __init__(self, *args):
		# Args is a sequence of either:
		# - column_name
		# - tuple of (column_name, column_type, format_string)
		# - tuple of (column_name, column_type, format_string, length_limit)
		# - tuple of (column_name, format_string)
		# - tuple of (column_name, format_string, length_limit)
		# - tuple of (column_name, column_type)
		# - tuple of (column_name, column_type, length_limit)
		# - tuple of (column_type, format_string)
		# - tuple of (column_type, format_string, length_limit)
		# ... where column_name is like "ID", "Name", etc.
		# ... and column_type is like int, str, etc.
		# ... and format_string is like "%.1f", "$%.2f", "%03d", "%s", etc.

		from crowdlib.utility.miscellaneous import namedtuple
		from crowdlib.utility.type_utils import is_string, is_sequence, is_type, is_int
		TableColumn = namedtuple("TableColumn", ("column_name", "column_type", "format_string", "length_limit"))

		self.columns = []

		def type_char(ob):
			if is_string(ob):
				return "S"
			elif is_type(ob):
				return "T"
			elif is_int(ob):
				return "I"
			else:
				return "?"

		for arg in args:
			column_name = ""
			column_type = None
			format_string = None
			length_limit = None
			if is_string(arg):
				column_name = arg
			elif is_sequence(arg):
				arg_type_str = "".join(type_char(piece) for piece in arg)
				if arg_type_str=="STS":
					column_name,column_type,format_string = arg
				elif arg_type_str=="STSI":
					column_name,column_type,format_string,length_limit = arg
				elif arg_type_str=="ST":
					column_name,column_type = arg
				elif arg_type_str=="STSI":
					column_name,column_type,length_limit = arg
				elif arg_type_str=="SS":
					column_name,format_string = arg
				elif arg_type_str=="SSI":
					column_name,format_string,length_limit = arg
				elif arg_type_str=="TS":
					column_type,format_string = arg
				elif arg_type_str=="TSI":
					column_type,format_string,length_limit = arg
				else:
					raise TypeError("Incorrect types for table column specification.  Got %s : %s"%(arg_type_str, repr(arg)))

			column = TableColumn(column_name=column_name, column_type=column_type, format_string=format_string, length_limit=length_limit)
			self.columns.append(column)
		self.columns = tuple(self.columns)
		self.rows = []
	
	def add_row(self, *values):
		if len(values) != len(self.columns):
			raise ValueError("Wrong number of columns for this table.  Table has %d columns.  Got %d values."%(len(self.columns), len(values)))
		# What was this supposed to do?  (found and disabled on 12/3/2013)
		#for i,val in enumerate(values):
		#	column_type = self.columns[i].column_type
		self.rows.append(values)
	
	def _column_names(self):
		if not any(len(col.column_name)>0 for col in self.columns):  # WHY???  (ajq, 7/25/2011)
			return None
		else:
			return tuple((col.column_name if col.column_name is not None else "") for col in self.columns)

	def _rendered_rows(self):
		from crowdlib.utility.type_utils import to_unicode
		for row in self.rows:
			pieces = []
			for i,value in enumerate(row):
				format_string = self.columns[i].format_string
				if format_string is not None:
					if hasattr(value, "strftime"):
						piece = value.strftime(format_string)
					else:
						piece = format_string%value
				else:
					piece = to_unicode(value)
				length_limit = self.columns[i].length_limit
				if length_limit is not None:
					piece = _truncate(piece, length_limit)
				pieces.append(piece)
			rendered_row = tuple(pieces)  # tuple of strings
			yield rendered_row

	def render_html(self):  # HTML 4, not XHTML
		from xml.sax.saxutils import escape

		def smooth(s):
			s = s.replace("\r\n","\n")
			s = escape(s, {"\n":"<br>", '"':"&quot;"})
			return s

		lines = []

		lines.append('<table border="1">')

		# Column headers
		column_names = self._column_names()
		if column_names is not None:
			lines.append('  <tr>')
			for i,column_name in enumerate(column_names):
				lines.append('    <td>%s</td>  <!-- %d -->'%(smooth(column_name), i))
			lines.append('  </tr>')

		# Data rows
		for rendered_row in self._rendered_rows():
			lines.append('  <tr>')
			for row_part in rendered_row:
				lines.append('    <td>%s</td>'%smooth(row_part))
			lines.append('  </tr>')

		lines.append('</table>')
		rendered_table = "\n".join(lines)
		return rendered_table

	def render_tab_delimited(self):  # Tuned for Excel's handling of quotes and multiline fields.
		column_names = self._column_names()
		bad_chars = ("\n", "\r", "\t")
		lines = []
		if column_names is not None:
			lines.append("\t".join(column_names))
		for rendered_row in self._rendered_rows():
			line_parts = []
			for row_part in rendered_row:
				line_part = row_part
				if any(bad_char in line_part for bad_char in bad_chars):
					# Gotta quote
					line_part = line_part.replace('"', '""')  # For Excel
					line_part = '"' + line_part + '"'
				line_parts.append(line_part)
			line = "\t".join(line_parts)
			lines.append(line)
		rendered_table = "\n".join(lines)
		return rendered_table


def _preformat_report(seq_of_seqs, headers_embedded, float_fmt, datetime_fmt, date_fmt, time_fmt, int_fmt, str_fmt, bool_vals_tf):
	# If embedded_headers is True, it means that every item is a 2-tuple of
	# the corresponding header and its data, like:
	# 	[(("name": "Barack Obama"),    ("address": "123 Penn")),
	# 	 (("name": "Hillary Clinton"), ("address": "234 Dipp"))]
	# This can be a convenient way to ensure that headers remain consistent
	# with the data when generating reports, even though it wastes some
	# memory.
	from datetime import datetime, date, time
	from crowdlib.utility.type_utils import is_string

	if bool_vals_tf[0].lower() in ("false", "f", "no", "n", "0", "off"):
		raise ValueError("bool_vals_tf seems to be backwards.  The first value should be for True")
	if bool_vals_tf[1].lower() in ("true", "t", "yes", "y", "1", "on"):
		raise ValueError("bool_vals_tf seems to be backwards.  The second value should be for False")
	if bool_vals_tf[0]==bool_vals_tf[1]:
		raise ValueError("bool_vals_tf shoud be a 2-tuple for True/False that must be different.")
		
	for i,seq in enumerate(seq_of_seqs):
		if headers_embedded==True:
			if i==0:
				headers = tuple(item[0] for item in seq)
				yield headers
			seq = tuple(item[1] for item in seq)
		parts = []
		for item in seq:
			if is_string(item):
				parts.append(str_fmt%item)
			elif isinstance(item, datetime):
				parts.append(item.strftime(datetime_fmt))
			elif isinstance(item, date):
				parts.append(item.strftime(date_fmt))
			elif isinstance(item, time):
				parts.append(item.strftime(time_fmt))
			elif isinstance(item, int):
				parts.append(int_fmt%item)
			elif isinstance(item, float):
				parts.append(float_fmt%item)
			elif isinstance(item, bool):
				if item==True:
					parts.append(bool_vals_tf[0])
				elif item==False:
					parts.append(bool_vals_tf[1])
				parts.append(int_fmt%item)
			else:
				parts.append(str(item))
		#lines.append(parts)
		yield parts

# Never called
#def format_table_txt_lines(seq_of_seqs, delimiter="\t", headers=None, headers_embedded=False, float_fmt="%.2f", datetime_fmt="%m/%d/%Y %H:%M:%S", date_fmt="%m/%d/%Y", time_fmt="%H:%M:%S", int_fmt="%d", str_fmt="%s", bool_vals_tf=("True","False"), newline="\n"):
#	lines = _preformat_report(seq_of_seqs, headers_embedded=headers_embedded,
#			float_fmt=float_fmt, datetime_fmt=datetime_fmt, date_fmt=date_fmt, time_fmt=time_fmt,
#			int_fmt=int_fmt, str_fmt=str_fmt, bool_vals_tf=bool_vals_tf)
#	return (delimiter.join(line) for line in lines)


# Never called
#def format_table_txt(seq_of_seqs, delimiter="\t", headers=None, headers_embedded=False, float_fmt="%.2f", datetime_fmt="%m/%d/%Y %H:%M:%S", date_fmt="%m/%d/%Y", time_fmt="%H:%M:%S", int_fmt="%d", str_fmt="%s", bool_vals_tf=("True","False"), newline="\n"):
#	from crowdlib.utility.type_utils import is_sequence_of_strings, is_string, to_tuple_if_non_sequence_iterable
#
#	lines = _preformat_report(seq_of_seqs, headers_embedded=headers_embedded,
#			float_fmt=float_fmt, datetime_fmt=datetime_fmt, date_fmt=date_fmt, time_fmt=time_fmt,
#			int_fmt=int_fmt, str_fmt=str_fmt, bool_vals_tf=bool_vals_tf)
#	
#	# Now lines is a tuple of tuples of formatted values.
#	assert all(is_sequence_of_strings(line) for line in lines)
#
#	lines = tuple(delimiter.join(parts) for parts in lines)
#
#	# Now lines is a tuple of formatted strings.
#	assert is_sequence_of_strings(lines), lines
#
#	rpt = newline.join(lines)
#
#	# Now rpt is the full report.
#	assert is_string(rpt)
#
#	return rpt


def _truncate(s, length_limit, ellipsis="..."):
	ellipsis_length = len(ellipsis)
	if len(s) > length_limit:
		s = s[:(length_limit - ellipsis_length)] + ellipsis
	return s
