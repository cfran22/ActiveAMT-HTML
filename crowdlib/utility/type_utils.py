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

from crowdlib.utility.time_utils import now_local, to_local_if_naive

try:
	# Python 2.x
	STRING_BASE_CLASS = basestring # includes str and unicode
except NameError:
	# Python 3.x
	STRING_BASE_CLASS = str # includes str (but not bytes)

def is_string(s):
	return isinstance(s, STRING_BASE_CLASS)

def is_unicode(s):
	# Python 2.x:  true iff s is a unicode
	# Python 3.x:  true iff s is a str
	try:
		# Python 2.x
		return isinstance(s,unicode)
	except NameError:
		# Python 3.x
		return isinstance(s,str)

def is_bytes(s):
	# Return True only if this is Python 3.x and s is a bytes object.
	return isinstance(s,bytes) and hasattr(s,"decode") and not hasattr(s,"encode")
	# Notes:  The bytes(...) function and the b"" syntax are both supported in
	# Python 2.6+.  bytes is a synonym for str in Python 2.6+.  Some aspects
	# are said to be different from Python 3.0+.
	#    http://docs.python.org/whatsnew/2.6.html
	# Notably, the Python 3.x "bytes" type does not have an encode method, thought
	# it does have a decode method.

def to_unicode(s, encoding="utf8"):
	# For Python 3.x, convert to str object.
	# For Python 2.x, convert to unicode object.

	if is_unicode(s):
		# Is str in Py3 or unicode in Py2.
		return s
	elif is_bytes(s):
		# Is bytes in Py3.  Doesn't apply in Py2.
		return s.decode(encoding)
	else:
		try:
			if isinstance(s,str):
				return unicode(s, encoding)
			else:
				return unicode(s)
		except NameError:
			return str(s)

def to_ascii(s, errors="backslashreplace"):
	# This works in both Python 2 and 3.  (confirmed 10-9-2011)
	# Input:  str (Python 2 or 3) or unicode (Python 2)
	# Output:  unicode (Python 2) or str (Python 3)
	return s.encode("ascii",errors).decode("ascii")

def is_datetime(o):
	from datetime import datetime
	return isinstance(o, datetime)

def to_boolean(s):
	if s in (True, False):
		return s
	elif s.lower() in ("true","1"):
		return True
	elif s.lower() in ("false","0"):
		return False
	else:
		raise ValueError("Cannot interpret %s as a boolean."%s)

def is_int(o):
	return isinstance(o, int)

def to_number(s):
	n = None
	if is_number(s):
		n = s
	else:
		try:
			n = int(s)
		except ValueError:
			try:
				n = float(s)
			except ValueError:
				raise ValueError("Can't convert %s to a number."%(str(s)))
	return n

def _make_cres(): # hide some of this mess from the namespace
	import re
	date_ptn = (
		r'(?P<y_or_m>\d{1,4})'      # year  if yyyy-mm-dd order, or month if mm-dd-yyyy order
		r'(?P<date_separator>[/-])' # separator, either - or /
		r'(?P<m_or_d>\d{1,2})'      # month if yyyy-mm-dd order, or day   if mm-dd-yyyy order
		r'\2'                       # separator, either - or / and must match first one
		r'(?P<d_or_y>\d{1,4})'      # day   if yyyy-mm-dd order, or year  if mm-dd-yyyy order
	)

	date_time_separator_ptn = r'(?:T?\s+)' # separator between date and time, "T" for ISO, otherwise " "

	time_ptn = (
		r'(?P<H>[012]?\d)'          # hour
		r':'                        # colon
		r'(?P<M>\d\d)'              # month
		r'(?::'                     # colon
		r'(?P<S>\d\d)'              # second (optional)
		r'(?:\.'                    # dot before seconds decimal portion (optional)
		r'(?P<f>\d{1,6})'           # microseconds (optional)
		r')?'                       # end microseconds
		r')?'                       # end seconds
		r'(?: '                     # space before AM/PM (optional)
		r'(?P<p>AM|PM|am|pm)'       # AM/PM
		r')?'                       # end AM/PM
	)

	date_time_cre = re.compile('^' + date_ptn + date_time_separator_ptn + time_ptn + '$')
	#import pyperclip; pyperclip.setcb(_DATE_TIME_CRE.pattern)
	date_cre = re.compile('^' + date_ptn + '$')
	return date_time_cre,date_cre

_DATE_TIME_CRE,_DATE_CRE = _make_cres()
del _make_cres

def _parse_date_time_string(s):
	# AMT returns time in this format:
	# 2012-07-14T00:56:40Z
	import datetime
	g = _DATE_TIME_CRE.match(s).groupdict("")
	if len(g["y_or_m"]) >= 3:
		year,month,day = int(g["y_or_m"]),int(g["m_or_d"]),int(g["d_or_y"])
	else:
		month,day,year = int(g["y_or_m"]),int(g["m_or_d"]),int(g["d_or_y"])
	hour = int(g["H"])
	minute = int(g["M"])
	second = int(g["S"] or 0)
	microsecond = int(g["f"].ljust(6, 0))
	ampm = g["p"]
	assert ampm in ("AM", "PM", "am", "pm", ""), ampm
	if ampm:
		if not 1 <= hour <= 12:
			raise ValueError("if AM/PM is specified then hour must be in the range 1..12 but got %r"%hour)
		elif hour == 12:
			if ampm == "AM" or ampm == "am":
				hour = 0
		elif ampm == "PM" or ampm == "pm":
			hour += 12
	return datetime.datetime(year, month, day, hour, minute, second, microsecond)


def to_date_time(o, allow_coalesce_to_duration=True, default_time=None):
	import datetime, time
	from crowdlib.all_exceptions import CannotInterpretDateTimeError, CannotInterpretDurationError, \
	                                    CannotInterpretDateError, CannotInterpretTimeError
	from crowdlib.utility.time_utils import TIME_ZONE_LOCAL, TIME_ZONE_UTC
	dt = None

	if isinstance(o, datetime.datetime):
		dt = o
	else:
		if is_string(o):
			_o = to_unicode(o)
			if ":" in _o:
				formats = (
					# Year first, UTC time, 24-hour
				   ("%Y-%m-%dT%H:%M:%SZ", "UTC"),
				   ("%Y-%m-%dT%H:%M:%S.%fZ", "UTC"),

					# Year first, local time, 24-hour
				   ("%Y-%m-%d %H:%M:%S.%f", "local"),
				   ("%Y-%m-%dT%H:%M:%S.%f", "local"),
				   ("%Y-%m-%d %H:%M:%S", "local"),
				   ("%Y-%m-%dT%H:%M:%S", "local"),

					# Month first, local time, AM/PM
				   ("%m/%d/%Y %I:%M:%S %p", "local"),  # added 20110803
				   ("%m-%d-%Y %I:%M:%S %p", "local"),  # added 20110803
				   ("%m/%d/%Y %I:%M %p", "local"),  # added 20110803
				   ("%m-%d-%Y %I:%M %p", "local"),  # added 20110803

					# Month first, local time, 24-hour time
				   ("%m/%d/%Y %H:%M:%S", "local"),
				   ("%m/%d/%Y %H:%M", "local"), # added 20110803
				   ("%m-%d-%Y %H:%M:%S", "local"),  # added 20110803
				   ("%m-%d-%Y %H:%M", "local"),  # added 20110803
				)
				for fmt,time_zone in formats:
					try:
						dt = datetime.datetime.strptime( _o, fmt )
						if time_zone=="UTC":
							t = time.time()
							offset = datetime.datetime.utcfromtimestamp(t) - datetime.datetime.fromtimestamp(t)
							dt -= offset
							if dt.tzinfo is None:
								dt = dt.replace(tzinfo=TIME_ZONE_UTC)
						elif time_zone=="local":
							if dt.tzinfo is None:
								dt = dt.replace(tzinfo=TIME_ZONE_LOCAL)
						else:
							assert False, "Shouldn't get here.  (err0859)"
					except ValueError:
						pass
					else:
						break
			elif default_time is not None and "T" not in _o and "Z" not in _o:
				try:
					dt = datetime.datetime.combine(to_date(_o), to_time(default_time))
					dt = dt.replace(tzinfo=TIME_ZONE_LOCAL)
				except CannotInterpretDateError:
					pass
				except CannotInterpretTimeError:
					pass
	if dt is None and allow_coalesce_to_duration:
		try:
			td = to_duration(o, allow_coalesce_to_datetime=False)  # allow_coalesce_to_datetime must be False to avoid infinite loop.
			dt = now_local() + td
		except CannotInterpretDurationError:
			pass

	if dt is None:
		# Try interpreting as a duration.
		raise CannotInterpretDateTimeError(repr(o))
	
	assert isinstance(dt, datetime.datetime)

	dt = to_local_if_naive(dt)
	assert isinstance(dt, datetime.datetime)

	return dt

def to_date(o):
	import datetime
	if isinstance(o, datetime.date):
		return o
	else:
		date_formats = ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d")
		if is_string(o):
			_o = to_unicode(o)
			for fmt in date_formats:
				try:
					dt = datetime.datetime.strptime(_o, fmt)
				except ValueError:
					pass
				else:
					return dt.date()
		from crowdlib.all_exceptions import CannotInterpretDateError # a subclass of ValueError
		raise CannotInterpretDateError("%r does not match any of %r"%(o, date_formats))

def to_time(o):
	import datetime
	if isinstance(o, datetime.time):
		return o
	else:
		time_formats = ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p")
		if is_string(o):
			_o = to_unicode(o)
			for fmt in time_formats:
				try:
					dt = datetime.datetime.strptime(_o, fmt)
				except ValueError:
					pass
				else:
					return dt.time()
		from crowdlib.all_exceptions import CannotInterpretTimeError # a subclass of ValueError
		raise CannotInterpretTimeError("%r does not match any of %r"%(o, time_formats))

def to_duration(o, allow_coalesce_to_datetime=True):
	import re, datetime
	from crowdlib.all_exceptions import CannotInterpretDurationError, CannotInterpretDateTimeError
	td = None
	if isinstance(o, datetime.timedelta):
		td = o
	elif is_number(o):
		td = datetime.timedelta(seconds=o)
	elif is_string(o):
		try:
			n = to_number(o)
			td = datetime.timedelta(seconds=n)
		except ValueError:
			mo = re.match(r"^(?P<sign>-)?(?P<whole_part>\d+)(?P<decimal_part>\.\d+)? (?P<unit>second|minute|hour|day|week)s?$", o)
			if mo is not None:
				whole_part = mo.group("whole_part")
				decimal_part = mo.group("decimal_part")
				unit = mo.group("unit")
				if decimal_part is None:
					n = int(whole_part)
				else:
					n = float(whole_part + decimal_part)
				if mo.group("sign")=="-":
					n = -1 * n
				multipliers = {
					"second" : 1,
					"minute" : 60,
					"hour"   : 60 * 60,
					"day"    : 60 * 60 * 24,
					"week"   : 60 * 60 * 24 * 7
				}
				multiplier = multipliers[unit]
				seconds = n * multiplier
				td = datetime.timedelta(seconds=seconds)
	if td is None and allow_coalesce_to_datetime:
		# Try to interpret as a datetime
		try:
			dt = to_date_time( o, allow_coalesce_to_duration=False )  # allow_coalesce_to_duration must be False to avoid infinite loop.
			td = dt - now_local()
		except CannotInterpretDateTimeError:
			pass
	if td is None:
		raise CannotInterpretDurationError(repr(o))
	
	assert isinstance(td, datetime.timedelta)
	return td

def coerce_to_date_time(s, interpret_durations_as_past, default_time=None):
	from crowdlib.all_exceptions import CannotInterpretDateTimeError, CannotInterpretDurationError
	if s is None:
		return None
	try:
		dt = to_date_time(s, allow_coalesce_to_duration=False, default_time=default_time)
	except CannotInterpretDateTimeError:
		try:
			dur = to_duration(s)
			if interpret_durations_as_past:
				dt = now_local() - dur
			else:
				dt = now_local() + dur
		except CannotInterpretDurationError:
			raise CannotInterpretDateTimeError(repr(s))
	return dt

def duration_to_seconds(td):
	return td.seconds + td.days * 60 * 60 * 24

def is_iterable(ob): # excluding strings
	return hasattr(ob, "__iter__") and not isinstance(ob, basestring)

def is_sequence_of_strings(ob):
	return is_sequence(ob) and all(isinstance(s, STRING_BASE_CLASS) for s in ob)

def is_sequence_of(ob,tp):
	return is_sequence(ob) and all(isinstance(item,tp) for item in ob)

def is_sequence(ob): # excluding strings
	#return isinstance(ob,tuple) or isinstance(ob,list)
	return hasattr(ob, "__getitem__") and is_iterable(ob)

def is_collection_of_strings(ob):
	return is_collection(ob) and all(isinstance(s, STRING_BASE_CLASS) for s in ob)

def is_collection_of(ob,tp):
	return is_collection(ob) and all(isinstance(item,tp) for item in ob)

def is_collection(ob): # excluding strings
	#return isinstance(ob,tuple) or isinstance(ob,list)
	return isinstance(ob, (tuple, list, set, frozenset)) or hasattr(ob, "__getitem__") and is_iterable(ob)

def to_tuple_if_non_sequence_iterable(ob):
	if is_sequence(ob):
		return ob
	elif is_iterable(ob):
		return tuple(ob)
	else:
		return ob

def is_type(ob):
	return isinstance(ob,type)

def is_number(ob):
	'''Return True iff ob is any kind of number (i.e. int, float, long, etc.) but I{not} a bool.'''
	import numbers
	return isinstance(ob,numbers.Number) and not isinstance(ob,bool)

#def _test():
#	print( to_date_time( "-2 hours" ) )
#	print( to_duration( "8/3/2011 3:00" ) )
#	print( to_date("1/1/2013") )
#	print( to_time("11:11:11") )
#	print( to_time("11:11:11.999999") )
#	print( to_date_time("1/1/2013", default_time="23:59:59.999999") )
#	print( to_date_time("11/1/2013", default_time="23:59:59.999999") )
#	print( coerce_to_date_time("11/1/2013", interpret_durations_as_past=True, default_time="00:00:00.000000") )
