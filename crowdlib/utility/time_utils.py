# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alex Quinn
@contact: aq@cs.umd.edu
@since: December 2013
'''

from __future__ import division, with_statement
import datetime, os, sys

# To ensure that the import statements within the pytz module work, we must temporarily add
# the crowdlib source directory to sys.path.
sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.."))
try:
	import pytz
except StandardError:
	from crowdlib import pytz

try:
	import tzlocal
except StandardError:
	from crowdlib import tzlocal
sys.path.pop()

TIME_ZONE_UTC = pytz.utc
TIME_ZONE_LOCAL = tzlocal.get_localzone()
	
_ISO_UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def parse_iso_utc_to_datetime_local(s):
	dt_naive = datetime.datetime.strptime(s, _ISO_UTC_FORMAT)
	dt_utc = dt_naive.replace(tzinfo=TIME_ZONE_UTC)
	dt_local = dt_utc.astimezone(TIME_ZONE_LOCAL)
	return dt_local

def format_datetime_to_iso_utc(dt):
	if dt.tzinfo is TIME_ZONE_UTC:
		dt_utc = dt
	else:
		dt_utc = dt.astimezone(TIME_ZONE_UTC)
	iso_utc = dt_utc.strftime(_ISO_UTC_FORMAT)
	return iso_utc

def now_local():
	return datetime.datetime.now(TIME_ZONE_LOCAL)

def now_utc():
	return datetime.datetime.now(TIME_ZONE_UTC)

def now_iso_utc():
	return datetime.datetime.now(TIME_ZONE_UTC).strftime(_ISO_UTC_FORMAT)

def to_utc_if_naive(dt):
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=TIME_ZONE_LOCAL)
	return dt

def to_local_if_naive(dt):
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=TIME_ZONE_LOCAL)
	return dt
