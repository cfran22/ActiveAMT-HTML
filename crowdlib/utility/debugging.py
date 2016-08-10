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

import os

def is_debugging():
	return "CROWDLIB_DEBUG" in os.environ or os.path.isfile(os.path.expanduser("~/.crowdlib_data/CROWDLIB_DEBUG"))

def dbg_log(*args, **kwargs):
	if is_debugging():
		from crowdlib.utility.console import log
		#log(*args, flag="[dbg]", **kwargs) # syntax error in Python 2.5
		kwargs["flag"] = "[dbg]"
		log(*args, **kwargs)

def get_call_stack_strs(clip_most_recent=0, include_only_paths_starting_with=None):
	import inspect, sys
	parts = []
	last_part = ""
	ellipsis = "..."
	case_sensitive_paths = (sys.platform != "win32")
	if not case_sensitive_paths:
		include_only_paths_starting_with = include_only_paths_starting_with.lower()
	include_only_paths_starting_with = include_only_paths_starting_with.replace("\\", "/")

	for stack_frame in inspect.stack()[clip_most_recent:]:
		frame,code_path,line_num,fn_name,code,code_idx = stack_frame # [pylint] allow unused variables : pylint:disable=W0612

		code_abs_path = os.path.abspath(code_path)
		if not case_sensitive_paths:
			code_abs_path = code_abs_path.lower()
		code_abs_path = code_abs_path.replace("\\", "/")

		if code_abs_path.startswith(include_only_paths_starting_with):
			code_filename = os.path.basename(code_path)
			part = "%s:%d(%s)"%(code_filename,line_num,fn_name)
		else:
			part = ellipsis

		if part != ellipsis or part != last_part:
			parts.append(part)

		last_part = part

	return tuple(parts)


