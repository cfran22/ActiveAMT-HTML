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

from crowdlib.utility.console import \
		clear_line, \
		dmp, \
		log

from crowdlib.utility.miscellaneous import \
		launch_url_in_browser_if_possible, \
		poll, \
		total_seconds

from crowdlib.utility.backports import \
		literal_eval, \
		namedtuple

from crowdlib.utility.debugging import \
		get_call_stack_strs

from crowdlib.utility.time_utils import \
		format_datetime_to_iso_utc, \
		now_iso_utc, \
		now_local, \
		now_utc, \
		parse_iso_utc_to_datetime_local, \
		to_local_if_naive, \
		to_utc_if_naive

from crowdlib.utility.type_utils import \
		coerce_to_date_time, \
		duration_to_seconds, \
		is_bytes, \
		is_collection, \
		is_collection_of, \
		is_collection_of_strings, \
		is_datetime, \
		is_iterable, \
		is_number, \
		is_sequence, \
		is_sequence_of, \
		is_sequence_of_strings, \
		is_string, \
		is_type, \
		is_unicode, \
		to_ascii, \
		to_boolean, \
		to_date, \
		to_date_time, \
		to_duration, \
		to_number, \
		to_tuple_if_non_sequence_iterable, \
		to_unicode

from crowdlib.utility.xml_helpers import \
		bool_in_element, \
		datetime_in_element, \
		dom_cdata, \
		dom_element, \
		duration_in_element, \
		is_valid_xml, \
		looks_like_limited_xhtml, \
		make_xml_document_root_element_fn_cdatas_fn, \
		number_in_element, \
		text_in_element, \
		text_node_content, \
		to_cdata, \
		xml_in_element, \
		xml2dom

from crowdlib.utility.tables import \
		Table

from crowdlib.utility.py23_compatibility import \
		urlencode_py23_compatible, \
		urlopen_py23_compatible, \
		urlretrieve_py23_compatible, \
		base64_encodestring_py23_compatible


#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# SHRAPNEL (delete any time if you don't think it will be needed)
#

# [no longer used as far as I know, 12/4/2013]
#from crowdlib.utility.files import \
#		tempfile_write, \
#		read_file, \
#		write_file

#from crowdlib.utility.console import \
#		dmp_pprint, \
#		dmp_xml, \
#		dmp_color, \
#		log_eval, \

#from crowdlib.utility.text import \
#		truncate, \
#		format_text_table, \
#		looks_like_url

#from crowdlib.utility.miscellaneous import \
#		switch_to_current_code_directory, \
#		get_hostname, \
#		round_up_to_multiple, \
#		get_crowdlib_dir, \
#		running_as_cgi, \
#		confirm, \

#from crowdlib.utility.debugging import \
#		PDB_BREAKPOINT

#from crowdlib.utility.datetime_formatting import \
#		parse_date_time, \
#		timestamp, \
#		time_iso8601, \
#		format_duration

#from crowdlib.utility.tables import \
#		format_table_txt_lines, \
#		format_table_txt, \

#try:
#	from crowdlib.utility.pyperclip import \
#			setcb as write_clipboard, \
#			getcb as read_clipboard
#except:
#	def write_clipboard(*args, **kwargs): # [pylint] args and kwargs are not used : pylint:disable=W0613
#		raise NotImplementedError("Clipboard operations are not available on this system.")
#	def read_clipboard(*args, **kwargs):  # [pylint] args and kwargs are not used : pylint:disable=W0613
#		raise NotImplementedError("Clipboard operations are not available on this system.")
