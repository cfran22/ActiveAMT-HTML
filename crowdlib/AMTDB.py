# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: January 2010
'''

# FIXME: The use of always_commit probably breaks any use of transactions.  Also, we
#        have no way to ensure all transactions are properly committed. (11-17-2013)

# TODO:  Store custom QualificationType info locally. (12/3/2013)

from __future__ import division, with_statement
import os, os.path, datetime, sqlite3, datetime, threading, collections
from crowdlib.utility import format_datetime_to_iso_utc, is_string, is_collection_of_strings, is_unicode, literal_eval, log, namedtuple, now_iso_utc, parse_iso_utc_to_datetime_local, total_seconds

try:
	import pysqlite2._sqlite as sqlite3
except ImportError:
	import sqlite3 # [pylint] reimport sqlite : pylint:disable=W0404

DATABASE_ERROR_BASE_CLASS = sqlite3.Error

_DBG_PRINT_QUERY_ON_ERROR = False
_UNDEFINED = object()


class AMTDB( object ):
	'''
	Encapsulates the database (currently implemented with SQLite3) and manages storing results and information
	about HITs.
	'''

	_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "sql/schema.sql")
	_thread_local_data = threading.local()
	_connections_weak_refs = []

	def open(self):  # called by AMT class
		# Don't actually open.  Just set a flag so we don't need to commit after
		# every non-SELECT query.  Trust the caller to close.
		self.always_commit = False

	def close(self):  # called by AMT class
		# Don't actually close.  Just commit and set a flag so we commit after
		# every non-SELECT query.
#		from crowdlib.utility import log
#		if self._get_all_connections_in_pool():
#			self.commit()
		self.always_commit = True

	def _log(self, s):
		if self._verbose:
			if not is_string(s):
				s = repr(s)
			s = "%s : %s"%(threading.current_thread().ident, s)
			log(s)
	
	def _make_where_clause_for_alphanumeric_ids(self, ids, column_name):
		assert is_collection_of_strings(ids), ids
		MAX_ID_LENGTH = 64
		if len(ids) == 0:
			raise ValueError("ids is empty")
		bad_ids = [i for i in ids if not i.isalnum() and 1 <= len(id) >= MAX_ID_LENGTH]
		if bad_ids:
			raise ValueError("Bad ID(s) found:  %r"%bad_ids)
		elif len(ids) == 1:
			the_id, = ids
			return '%s="%s"'%(column_name, the_id)
		else:
			assert len(ids) >= 2
			ids_quoted = (('"' + i + '"') for i in ids)
			return column_name + ' in (' + ','.join(ids_quoted) + ')'

	def _get_connection(self):
		current_thread_ident = threading.current_thread().ident
		thread_local_data = self.__class__._thread_local_data # [pylint] access private member : pylint:disable=W0212

		try:
			conn = thread_local_data.connection
			self._log("AMTDB._get_connection() : [R] Reused connection for thread %r."%current_thread_ident)
		except AttributeError:
			conn = sqlite3.connect(self._filename, detect_types=sqlite3.PARSE_DECLTYPES) # >= 11/17/2013
			thread_local_data.connection = conn
			conn.row_factory = sqlite3.Row
			self._log("AMTDB._get_connection() : [C] Created connection for thread %r."%current_thread_ident)
		return conn
	
	def __init__(self, filename, verbose=False, always_commit=False):
		self._filename = filename
		self._dirty_tables = set()
		self._verbose = verbose
		#self._conn = None
		self._conn_pool_by_thread_ident = {}

		self.always_commit = always_commit
		# If True, then always commit after any query other than SELECT.

		self.is_new = (not os.path.isfile(filename)) or (os.path.getsize(filename)==0)

		self._log( "Opened DB at %s"%filename )

		if self.is_new:
			conn = self._get_connection()
			self._log( "Creating tables...." )
			with open(self._SCHEMA_PATH, "rb") as infile:
				schema_sql = infile.read().decode("utf8")
			conn.executescript(schema_sql)
			#conn.commit() # disabled on 11/19/2013 FIXME
			#TODO:  Make sure it syncs after the DB is created.  Maybe require
			# an initial setup command or just do transparently in AMT.py.

	def _insert(self, table_name, vals, on_conflict=None):
		# Credit:  Taken from Alex's stevenjessebernstein.com project.
		assert on_conflict is None or on_conflict.lower() in ("rollback", "abort", "fail", "ignore", "replace")
		self._log(">>> INSERT into %s"%table_name)
		sql_parts = ["insert"]
		if on_conflict is not None:
			sql_parts += ["or", on_conflict]
		sql_parts += ["into", table_name]
		cols = []
		params = []
		for k,v in vals.items():
			cols.append(k)
			params.append(v)
		cols_list = ", ".join(cols)
		placeholders_list = ", ".join(("?",) * len(vals))
		sql_parts += ["(", cols_list, ")", "values", "(", placeholders_list, ");"]
		sql = " ".join(sql_parts)
		cur = self._query_get_cursor(sql, *params) # [pylint] tolerate *params magic : pylint:disable=W0142

		row_id = cur.lastrowid
		self._log("<<< /INSERT into %s"%table_name)
		return row_id

	################################################################################
	# Mechanics
	#
		
	def commit(self):
		'''
		Force the database to commit.
		@return: nothing
		'''
		conn = self._get_connection()
		conn.commit()
		self._log( "Did DB commit" )
	
	def query(self, sql, *params):
		# Do a raw SQL query against the SQLite database.  This is primarily used internally
		# but can also be used to run specialized reports.

		return self._query_get_cursor(sql, *params).fetchall()

	def _dump_query_on_error(self, sql, params):
		indent_spaces = 4
		lines = [l.strip() for l in sql.splitlines()]
		lines = [((" " * indent_spaces) + l) for l in lines if len(l)>0]
		sql = "\n".join(lines)
		if _DBG_PRINT_QUERY_ON_ERROR:
			print("")
			print("="*80)
			print("SQL:")
			print(sql)
			if len(params)>0:
				print("-"*40)
				print("Parameters:")
				for i,param in enumerate(params):
					num_str = "%d."%(i+1)
					indent_str = " "*(indent_spaces - len(num_str))
					print( num_str + indent_str + repr(param) ) 
			print("="*80)
			print("")

	def _query_get_cursor(self, sql, *params):
		# Do a raw SQL query against the SQLite database.  This is primarily used internally
		# but can also be used to run specialized reports.
		# 
		# sql (string) -- Raw SQL query to be run
		#
		# Returns: Cursor object from the sqlite3 module.

		conn = self._get_connection()
		while True:
			try:
				cursor = conn.execute(sql, params)
			except sqlite3.InterfaceError:
				self._dump_query_on_error(sql, params)
				raise
			except sqlite3.OperationalError:
				self._dump_query_on_error(sql, params)
				raise
			except ValueError:
				e = sys.exc_info()[1]
				print(sql)
				print(repr(params))
				print( repr(e.args) )
				raise
			break

		# Commit after every non-SELECT query iff always_commit==True
		if self.always_commit and not sql.lower().lstrip().startswith("select"):
			self.commit()

		return cursor

	def _count(self, table_name, where, *params):
		import re
		if re.match(r"^[a-zA-Z_]+$", table_name) is None:  # for safety
			raise ValueError("Table name must be a regular identifier")
		if re.match(r"^[a-zA-Z_ =]+$", where) is None:  # for safety
			raise ValueError("Where clause must be nothng but regular identifiers, equal signs, and spaces - very simple")
		sql = "select count(*) from " + table_name + " where " + where + ";"
		rows = self.query(sql, *params)
		return len(rows)

	def _query_single_value(self, sql, *params):
		rows = self.query(sql,*params)
		if len(rows)==0:
			return None
		elif len(rows)==1:
			return rows[0][0]
		else:
			assert False, "Shouldn't have >1 row for query: %s %s"%(sql,repr(params))


	################################################################################
	# HITs / HITTypes
	#

	def _make_hit_record_from_hit_row(self, row):
		"""Returns a HITRecordDB object"""
		from crowdlib.HITRecord import HITRecordDB
		hit_record = HITRecordDB(
				  creation_time=_parse_datetime(row[str("creation_time")]),
				  expiration_time=_parse_datetime(row[str("expiration_time")]),
				  hit_id=row[str("hit_id")],
				  hit_review_status=row[str("hit_review_status")],
				  hit_status=row[str("hit_status")],
				  hit_type_id=row[str("hit_type_id")],
				  max_assignments=row[str("max_assignments")],
				  num_pending=row[str("num_pending")],
				  num_available=row[str("num_available")],
				  num_completed=row[str("num_completed")],
				  question=row[str("question_xml")],
				  requester_annotation=row[str("requester_annotation")],
				  approximate_expiration_time=_parse_datetime(row[str("approximate_expiration_time")]),
		)
		return hit_record

	def get_hit_records(self, hit_type_id=None, hit_id=None):
		"""Returns an iterable (generator) of HITRecordDB objects."""

		assert (hit_type_id is None) or (hit_id is None)
		hit_records = []
		sql = 'select * from hit'
		if hit_type_id is not None:
			sql += ' where hit_type_id=?'
			params = (hit_type_id,)
		elif hit_id is not None:
			sql += ' where hit_id=?'
			params = (hit_id,)
		else:
			params = ()

		rows = self.query(sql, *params)            # [pylint] tolerate *params magic : pylint:disable=W0142

		for row in rows:
			hit_record = self._make_hit_record_from_hit_row(row=row)
			#yield hit_record
			hit_records.append(hit_record) # changed 11/19/2013
		return tuple(hit_records)
	
	def get_hit_ids(self):
		"""Returns a set of all HIT IDs in the database."""
		sql = 'select hit_id from hit'
		rows = self.query(sql)
		hit_ids = set(row[0] for row in rows)
		return hit_ids

	def get_hit_record(self, hit_id):
		from crowdlib.all_exceptions import HITNotFoundException
		hit_records = tuple(self.get_hit_records(hit_id=hit_id))
		if len(hit_records)==1:
			return hit_records[0]
		else:
			raise HITNotFoundException(hit_id)

	def put_hit(self,hit,replace_if_exists=True):
		if replace_if_exists:
			on_conflict = "replace"
		else:
			on_conflict = "abort"
		try:
			self._insert("hit", {
				"hit_id" : hit.id,
				"hit_type_id" : hit.hit_type.id,
				"creation_time" : _format_datetime(hit.creation_time),
				"hit_status" : hit.hit_status,
				"expiration_time" : _format_datetime(hit.expiration_time),
				"max_assignments" : hit.max_assignments,
				"requester_annotation" : hit.requester_annotation,
				"hit_review_status" : hit.hit_review_status,
				"num_pending" : hit.num_pending,
				"num_available" : hit.num_available,
				"num_completed" : hit.num_completed,
				"question_xml" : hit.question_xml,
				"approximate_expiration_time" : _format_datetime(hit.approximate_expiration_time)
				}, on_conflict=on_conflict)
			self._log( "put_hit: "+hit.id )
		except ValueError:  # should be an sqlite exception
			self.update_hit(
				hit_id=hit.id,
				hit_status=hit.hit_status,
				creation_time=hit.creation_time,
				expiration_time=hit.expiration_time,
				num_pending=hit.num_pending,
				num_available=hit.num_available,
				num_completed=hit.num_completed,
				max_assignments=hit.max_assignments,
				approximate_expiration_time=hit.approximate_expiration_time
			)
			self._log( "put_hit (as update): "+hit.id )

	def put_hit_type(self, hit_type):
		self._log( "put_hit_type: %s  (\"%s\")"%(hit_type.id, hit_type.title) )
		self._insert("hit_type", {
			"hit_type_id" : hit_type.id,
			"title" : hit_type.title,
			"description" : hit_type.description,
			"keywords" : _format_tuple(hit_type.keywords),
			"reward_amount" : hit_type.reward,
			"reward_currency" : hit_type.currency,
			"assignment_duration" : _format_duration(hit_type.time_limit),
			"auto_approval_delay" : _format_duration(hit_type.autopay_delay),
		}, on_conflict="ignore")

		for qr in hit_type.qualification_requirements:
			self._insert("hit_type_qualification_requirement", {
				"hit_type_id" : hit_type.id,
				"qualification_type_id" : qr.qualification_type_id,
				"comparator" : qr.comparator,
				"integer_value" : qr.integer_value,
				"locale_value" : qr.locale_value,
				"required_to_preview" : _format_bool(qr.required_to_preview),
			}, on_conflict="replace")
	
	def get_qualification_requirement_records_for_hit_type_id(self, hit_type_id):
		from crowdlib.QualificationRequirementRecord import QualificationRequirementRecord
		assert is_string(hit_type_id) and len(hit_type_id)>2
		sql = "select * from hit_type_qualification_requirement where hit_type_id=?;"
		rows = self.query(sql, hit_type_id)
		qualification_requirement_records = []
		for row in rows:
			integer_value = row[str("integer_value")],
			locale_value = row[str("locale_value")],
			assert (integer_value is None) ^ (locale_value is not None)
			qreq = QualificationRequirementRecord(
					qualification_type_id = row[str("qualification_type_id")],
					comparator = row[str("comparator")],
					integer_value = integer_value,
					locale_value = locale_value,
					required_to_preview = _parse_bool(row[str("required_to_preview")])
			)
			qualification_requirement_records.append(qreq)
		return qualification_requirement_records

	def _make_hit_type_record_from_hit_type_row(self, row):
		from crowdlib.HITRecord import HITTypeRecordDB
		from crowdlib.Reward import Reward
		reward = Reward(
		  amount = row[str("reward_amount")],
		  currency_code = row[str("reward_currency")],
		  formatted_price=None
		)
		hit_type_id = row[str("hit_type_id")]
		qual_req_records = self.get_qualification_requirement_records_for_hit_type_id(hit_type_id=hit_type_id)
		hit_type_record = HITTypeRecordDB(
			  assignment_duration = _parse_duration(row[str("assignment_duration")]),
			  auto_approval_delay = _parse_duration(row[str("auto_approval_delay")]),
			  description = row[str("description")],
			  hit_type_id = row[str("hit_type_id")],
			  keywords = _parse_tuple(row[str("keywords")]),
			  qualification_requirements=qual_req_records,
			  reward = reward,
			  title = row[str("title")],
		)
		return hit_type_record

	def _get_hit_type_records(self, hit_type_id=None): # GENERATOR
		sql = "select * from hit_type"

		if hit_type_id is None:
			rows = self.query(sql)
		else:
			sql += " where hit_type_id=?"
			rows = self.query(sql, hit_type_id)

		for row in rows:
			hit_type_record = self._make_hit_type_record_from_hit_type_row(row=row)
			yield hit_type_record

	def get_hit_type_records(self): # GENERATOR
		return self._get_hit_type_records()

	def set_notification_stopped(self):
		self.query("delete from notification_status")

	def set_notification_started(self, url):
		self.set_notification_stopped()
		self.query("update notification_status set url=?", url)
	
	def set_notification_test_received(self):
		self.query("update notification_status set test_received_time=?", now_iso_utc())

	def set_notification_hit_type_received(self, hit_type_id):
		self.query("update notification_hit_type set last_received_time=? where hit_type_id=?", now_iso_utc(), hit_type_id)

	def set_notification_hit_type_registered(self, hit_type_id):
		self._insert("notification_hit_type", dict(
			hit_type_id=hit_type_id,
			registered_time=now_iso_utc(),
			is_connected=_format_bool(False),
			last_received_time=None,
		), on_conflict="replace")

	def get_known_hit_ids_except_hit_status(self, hit_status):
		rows = self.query("select hit_id from hit where hit_status != ?", hit_status) # no particular order
		hit_ids = tuple(row[0] for row in rows)
		assert len(hit_ids) == len(set(hit_ids))
		return hit_ids

	def set_hit_statuses(self, hit_ids, hit_status):
		if len(hit_ids):
			self.update_hits(hit_ids, hit_status=hit_status)

#			where_clause = self._make_where_clause_for_alphanumeric_ids(ids=hit_ids, column_name="hit_id")
#			sql = "update hit set hit_status=? where " + where_clause
#			self.query(sql, hit_status)
	
	def set_notification_hit_type_unregistered(self, hit_type_id):
		self.query("delete from notification_hit_type where hit_type_id=?", hit_type_id)

	def set_notification_hit_type_is_connected(self, hit_type_id):
		self.query("update notification_hit_type set is_connected=? where hit_type_id=?", _format_bool(True), hit_type_id)

	def get_notification_hit_type_registration(self, hit_type_id):
		from crowdlib.all_exceptions import HITTypeNotFoundException
		rows = self.query("select registered_time, is_connected, last_received_time from notification_hit_type where hit_type_id=?",
				hit_type_id)
		if len(rows) == 1:
			test_received_time = _parse_datetime(self._query_single_value("select test_received_time from notification_status"))
			return NotificationHitTypeRegistration(
					test_received_time=test_received_time,
					registered_time = _parse_datetime(rows[0][0]),
					is_connected = _parse_bool(rows[0][1]),
					last_received_time = _parse_datetime(rows[0][2]),
			)
		elif len(rows) == 0:
			raise HITTypeNotFoundException(hit_type_id, "does not appear to be registered for notifications")
		else:
			assert False, "found %d rows but expected either 0 or 1"%len(rows)
	
	def get_notification_hit_type_ids_registered(self):
		rows = self.query("select hit_type_id from notification_hit_type")
		hit_type_ids = tuple(row[0] for row in rows)
		return hit_type_ids

	def get_hit_type_record(self, hit_type_id):
		from crowdlib.all_exceptions import HITTypeNotFoundException
		hit_type_records = tuple(self._get_hit_type_records(hit_type_id))
		if len(hit_type_records)==1:
			return hit_type_records[0]
		elif len(hit_type_records)==0:
			raise HITTypeNotFoundException(hit_type_id)
		else:
			assert False, "Should not have multiple rows in DB for HIT type ID %s"%hit_type_id
			
	def record_worker_message(self, worker_id, send_time, subject, message_text):
		self._insert("sent_mail", {
			"worker_id":worker_id,
			"send_time":_format_datetime(send_time),
			"subject":subject,
			"message_text":message_text
		})
	
	def record_worker_bonus(self, worker_id, assignment_id, amount, currency, payment_time, reason):
		self._insert("bonus", {
			"worker_id" : worker_id,
			"assignment_id" : assignment_id,
			"amount" : amount,
			"currency"   : currency,
			"payment_time" : _format_datetime(payment_time),
			"reason" : reason
		})
		


		

	################################################################################
	# Assignments
	#

	def put_assignment(self, assignment):
		self._insert("assignment", {
			"assignment_id" : assignment.id,
			"worker_id" : assignment.worker.id,
			"hit_id" : assignment.hit.id,
			"assignment_status" : assignment.assignment_status,
			"auto_approval_time" : _format_datetime(assignment.autopay_time),
			"accept_time" : _format_datetime(assignment.accept_time),
			"submit_time" : _format_datetime(assignment.submit_time),
			"approval_time" : _format_datetime(assignment.approval_time),
			"rejection_time" : _format_datetime(assignment.rejection_time),
			"requester_feedback" : assignment.requester_feedback
		}, on_conflict="ignore")
		for answer in assignment.answers:
			self.put_answer( answer, assignment.id )
	
	def count_assignments_for_hit_id(self, hit_id):
		sql = "select count(*) from assignment where hit_id=?;"
		num_asgs = self.query(sql, hit_id).fetch_all()[0]
		return num_asgs

	def update_assignment_approved(self, assignment_id, approval_time):
		sql = "update assignment set approval_time=?, assignment_status='Approved' where assignment_id=?;"
		self.query(sql, _format_datetime(approval_time), assignment_id)

	def update_assignment_rejected(self, assignment_id, rejection_time):
		sql = "update assignment set rejection_time=?, assignment_status='Rejected' where assignment_id=?;"
		self.query(sql, _format_datetime(rejection_time), assignment_id)

	def update_assignment(self, assignment_id, assignment_status=None, submit_time=None, approval_time=None, rejection_time=None, requester_feedback=None):
		sql = ("update assignment set ")
		params = []
		potential_params = (
				("assignment_status",assignment_status),
				("submit_time",_format_datetime(submit_time)),
				("approval_time",_format_datetime(approval_time)),
				("rejection_time",_format_datetime(rejection_time)),
				("requester_feedback",requester_feedback)
		)
		usable_params = tuple((pnm,pval) for (pnm,pval) in potential_params if pval is not None)
		assert len(usable_params) > 0
		sql += ", ".join("%s=?"%pnm for (pnm,pval) in usable_params)
		sql += " where assignment_id=?;"
		params = tuple(pval for (pnm,pval) in usable_params) + (assignment_id,)
		self.query(sql, *params)                   # [pylint] tolerate *params magic : pylint:disable=W0142

	def update_hits(self, hit_ids, hit_status=_UNDEFINED, creation_time=_UNDEFINED, expiration_time=_UNDEFINED, num_pending=_UNDEFINED,
			             num_available=_UNDEFINED, num_completed=_UNDEFINED, max_assignments=_UNDEFINED, approximate_expiration_time=_UNDEFINED):
		sql = ("update hit set ")
#		params = []
		set_parts = []
		query_params = []

		if hit_status is not None and hit_status is not _UNDEFINED:
			set_parts.append("hit_status=?")
			query_params.append(hit_status)
		if creation_time is not None and creation_time is not _UNDEFINED:
			set_parts.append("creation_time=?")
			query_params.append(_format_datetime(creation_time))
		if expiration_time is not None and expiration_time is not _UNDEFINED:
			set_parts.append("expiration_time=?")
			query_params.append(_format_datetime(_format_datetime(expiration_time)))
		if num_pending is not None and num_pending is not _UNDEFINED:
			set_parts.append("num_pending=?")
			query_params.append(num_pending)
		if num_available is not None and num_available is not _UNDEFINED:
			set_parts.append("num_available=?")
			query_params.append(num_available)
		if num_completed is not None and num_completed is not _UNDEFINED:
			set_parts.append("num_completed=?")
			query_params.append(num_completed)
		if max_assignments is not None and max_assignments is not _UNDEFINED:
			set_parts.append("max_assignments=?")
			query_params.append(max_assignments)
		if approximate_expiration_time is not _UNDEFINED:
			if approximate_expiration_time is None:
				set_parts.append("approximate_expiration_time=NULL")
			else:
				set_parts.append("approximate_expiration_time=?")
				query_params.append(_format_datetime(approximate_expiration_time))

		assert len(set_parts) >= 1
		assert len(set_parts) in (len(query_params), len(query_params)-1) # might have one less due to approximate_expiration_time

		sql += ", ".join(set_parts)
		sql += " where " + self._make_where_clause_for_alphanumeric_ids(ids=hit_ids, column_name="hit_id")
		self.query(sql, *query_params)  # [pylint] Tolerate *params magic : pylint:disable=W0142

		#sql += ", ".join("%s=?"%pnm for (pnm,pval) in usable_params)
		#sql += "where hit_id=?;"
		#params = tuple(pval for (pnm,pval) in usable_params) + (hit_id,)
		#self.query(sql, *params)  # [pylint] Tolerate *params magic : pylint:disable=W0142
	
	def update_hit(self, hit_id, *args, **kwargs):
		self.update_hits(hit_ids=(hit_id,), *args, **kwargs)

	def set_hit_approximate_expiration_time(self, hit_id, approximate_expiration_time):
		self.update_hit(hit_id=hit_id, approximate_expiration_time=approximate_expiration_time)
		#sql.query("update hit set approximate_expiration_time=? where hit_id=?", (approximate_expiration_time, hit_id))

	def update_worker_blocked(self, worker_id, reason):
		# Reason may be None
		self._insert("worker_block", {"worker_id":worker_id, "reason":reason}, on_conflict="replace")

	def update_worker_unblocked(self, worker_id):
		sql = "delete from worker_block where worker_id=?;"
		self.query(sql, worker_id)

	def is_worker_id_blocked(self, worker_id):
		num_rows = self._count("worker_block", "worker_id=?", worker_id)
		assert num_rows in (0,1), "Shouldn't have >1 row for a given worker!"
		return (num_rows==1)
	
	def get_worker_block_reason(self, worker_id):
		from crowdlib.all_exceptions import WorkerNotFoundException
		reason = self._query_single_value("select reason from worker_block where worker_id=?;", worker_id)
		if reason is None:
			raise WorkerNotFoundException(worker_id)
		return reason
	
	def get_hit_id_for_assignment_id(self,assignment_id):
		from crowdlib.all_exceptions import AssignmentNotFoundException
		hit_id = self._query_single_value("select hit_id from assignment where assignment_id=?", assignment_id)
		if hit_id is None:
			raise AssignmentNotFoundException(assignment_id)
		return hit_id

	def get_hit_type_id_for_hit_id(self, hit_id):
		from crowdlib.all_exceptions import HITNotFoundException
		hit_type_id = self._query_single_value("select hit_type_id from hit where hit_id=?;", hit_id)
		if hit_type_id is None:
			raise HITNotFoundException(hit_id)
		return hit_type_id


	def get_assignment_record(self, assignment_id):
		from crowdlib.all_exceptions import AssignmentNotFoundException
		assignment_records = tuple(self.get_assignment_records(assignment_id=assignment_id))
		if len(assignment_records)==1:
			assignment_record = assignment_records[0]
			return assignment_record
		else:
			raise AssignmentNotFoundException(assignment_id=assignment_id)
		
	def get_assignment_records(self, hit_id=None, assignment_id=None):    # GENERATOR
		# If assignment_id is specified, we will filter and retrieve only that assignment.

		from crowdlib.AssignmentRecord import AssignmentRecord
		from crowdlib.AnswerRecord import AnswerRecord

		assert (hit_id is None) or (assignment_id is None), "Do not pass both assignment_id and hit_id - one or the other, please."
		assert (hit_id is None) or is_unicode(hit_id), hit_id
		assert (assignment_id is None) or is_unicode(assignment_id)

		sql = """\
			select
				assignment.assignment_id as assignment_id,
				assignment.worker_id as worker_id,
				assignment.hit_id as hit_id,
				assignment.assignment_status as assignment_status,
				assignment.auto_approval_time as auto_approval_time,
				assignment.accept_time as accept_time,
				assignment.submit_time as submit_time,
				assignment.approval_time as approval_time,
				assignment.rejection_time as rejection_time,
				assignment.requester_feedback as requester_feedback,
				answer.task_id as task_id,
				answer.answer_type as answer_type,
				answer.free_text as free_text,
				answer.selection_id as selection_id,
				answer.other_selection_text as other_selection_text,
				answer.uploaded_file_key as uploaded_file_key,
				answer.uploaded_file_size as uploaded_file_size
			from
				assignment
				inner join answer using (assignment_id)"""

		if hit_id is not None:
			sql += "\n\t\t\twhere\n\t\t\t\tassignment.hit_id=?"
			params = (hit_id,)
		elif assignment_id is not None:
			sql += "\n\t\t\twhere\n\t\t\t\tassignment.assignment_id=?"
			params = (assignment_id,)
		else:
			params = ()

		sql += "\n\t\t\torder by\n\t\t\t\tassignment.assignment_id asc"

		last_assignment_id = None
		rows = self.query(sql, *params)            # [pylint] tolerate *params magic : pylint:disable=W0142
		
		assignment_record = None
		for row in rows:
			assignment_id = row[str("assignment_id")]
			if assignment_id != last_assignment_id:

				if last_assignment_id is not None:
					yield assignment_record  # Last assignment will be yielded from below.

				answer_records = []
				if hit_id is not None:
					assert row[str("hit_id")]==hit_id, "%s != %s"%(repr(row[str("hit_id")]), repr(hit_id))
				assignment_record = AssignmentRecord(
					assignment_id = row[str("assignment_id")],
					worker_id = row[str("worker_id")],
					hit_id = row[str("hit_id")],
					assignment_status = row[str("assignment_status")],
					auto_approval_time = _parse_datetime(row[str("auto_approval_time")]),
					accept_time = _parse_datetime(row[str("accept_time")]),
					submit_time = _parse_datetime(row[str("submit_time")]),
					approval_time = _parse_datetime(row[str("approval_time")]),
					rejection_time = _parse_datetime(row[str("rejection_time")]),
					requester_feedback = row[str("requester_feedback")],
					answer_records = answer_records,
				)
				last_assignment_id = assignment_id

			answer_record = AnswerRecord(
#					assignment_id=assignment_id,
					question_identifier=row[str("task_id")],
					free_text=row[str("free_text")],
					selection_identifier=row[str("selection_id")],
					other_selection=row[str("other_selection_text")],
					uploaded_file_key=row[str("uploaded_file_key")],
					uploaded_file_size_in_bytes=row[str("uploaded_file_size")])

			answer_records.append(answer_record)

		if last_assignment_id is not None:
			assert isinstance(assignment_record, AssignmentRecord)
			assert all(isinstance(asr,AnswerRecord) for asr in assignment_record.answer_records)
			yield assignment_record  # Previous assignments were yielded from above.


	def put_answer(self, answer, assignment_id):
		# DO NOT CALL answer.assignment HERE.  IT WILL CREATE INFINITE RECURSION.
		from crowdlib.Answer import AnswerFreeText, AnswerSelection, AnswerUploadedFile
		# from crowdlib.Answer import AnswerBlank  # Why did we need this again?
		answer_id = answer.question_id + "-" + assignment_id
		free_text            = answer.free_text            if isinstance(answer,AnswerFreeText)    else None
		selection_id         = answer.selection_id         if isinstance(answer,AnswerSelection)    else None
		other_selection_text = answer.other_selection_text if isinstance(answer,AnswerSelection)    else None
		uploaded_file_key    = answer.uploaded_file_key    if isinstance(answer,AnswerUploadedFile) else None
		uploaded_file_size   = answer.uploaded_file_size   if isinstance(answer,AnswerUploadedFile) else None
		self._insert("answer", {
			"answer_id" : answer.id,
			"assignment_id" : assignment_id,
			"task_id" : answer.question_id,
			"answer_type" : answer.answer_type,
			"free_text" : free_text,
			"selection_id" : selection_id,
			"other_selection_text" : other_selection_text,
			"uploaded_file_key" : uploaded_file_key,
			"uploaded_file_size" : uploaded_file_size,
		}, on_conflict="replace")
		self._log( "put_answer:  %s / %s"%(answer_id, assignment_id) )
	
	def _make_where_clause(self,conditions):
		if len(conditions)==0:
			return ""
		else:
			return "WHERE" + " AND ".join("(%s)"%cond for cond in conditions)

	def get_bonuses(self, assignment_id, worker_id): # GENERATOR
		from crowdlib.BonusRecord import BonusRecord
		sql = """\
		select assignment_id, worker_id, amount, currency, payment_time, reason
		from bonus
		"""
		conditions = []
		params = []
		if assignment_id is not None:
			conditions.append("assignment_id=?")
			params.append(assignment_id)
		if worker_id is not None:
			conditions.append("worker_id=?")
			params.append(worker_id)
		sql += self._make_where_clause(conditions)
		rows = self.query(sql, *params)            # [pylint] tolerate *params magic : pylint:disable=W0142
		for row in rows:
			bonus_record = BonusRecord(
				assignment_id=row[str("assignment_id")],
				worker_id=row[str("worker_id")],
				amount=row[str("amount")],
				currency=row[str("currency")],
				payment_time=_parse_datetime(row[str("payment_time")]),
				reason=row[str("reason")],
			)
			yield bonus_record

NotificationHitTypeRegistration = namedtuple("NotificationHitTypeRegistration",
		("test_received_time", "registered_time", "is_connected", "last_received_time"))

def _format_datetime(dt):
	if dt is None:
		return dt
	else:
		return format_datetime_to_iso_utc(dt)

def _parse_datetime(s):
	if s:
		return parse_iso_utc_to_datetime_local(s)
	else:
		return None

def _format_bool(b):
	if b is None:
		return None
	elif b == True:
		return 1
	elif b == False:
		return 0
	else:
		raise ValueError("Invalid value for bool:  %r"%b)

def _parse_bool(s):
	if s is None:
		return None
	elif s == 1:
		return True
	elif s == 0:
		return False
	else:
		raise ValueError("Invalid value for bool:  %r"%s)

def _format_tuple(t):
	if t is None:
		return t
	else:
		return repr(t)

def _parse_tuple(s):
	if s is None:
		return s
	else:
		return literal_eval(s)

def _format_duration(d):
	if d is None:
		return None
	else:
		return int(round(total_seconds(d),0))

def _parse_duration(d):
	if d is None:
		return None
	else:
		return datetime.timedelta(seconds=d)



#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# EXPERIEMENTAL CODE (do not delete, yet)
#

#	def is_notification_started_and_tested(self):
#		rows = self.query("select test_received_time from notification_status")
#		assert len(rows) in (0, 1)
#		is_started = False
#		is_tested = False
#		if len(rows) == 1:
#			is_started = True
#			is_tested  = (rows[0][0] is not None)
#		elif len(rows) == 0:
#			is_started = False
#			is_tested  = False
#		else:
#			assert False
#		return (is_started, is_tested)

#	def get_hit_type_notification_url(self, hit_type_id):
#		from crowdlib.all_exceptions import NotificationsAddressNotFoundException
#		sql = "select url from hit_type_notification_address where hit_type_id=?"
#		url = self._query_single_value(sql, hit_type_id)
#		if url is None:
#			raise NotificationsAddressNotFoundException(hit_type_id)
#		else:
#			return url

#	def put_hit_type_notification_url(self, hit_type_id, url):
#		if url is None:
#			self.query("delete from hit_type_notification_address where hit_type_id=?", hit_type_id)
#		else:
#			self._insert("hit_type_notification_address", {
#						 "hit_type_id" : hit_type_id,
#						 "url" : url},
#						 on_conflict="abort")
#		return url


#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# SHRAPNEL (delete any time if you don't think it will be needed)
#
#	def update_hit(self, hit_id, hit_status=None, creation_time=None, expiration_time=None, num_pending=None,
#			           num_available=None, num_completed=None, max_assignments=None, approximate_expiration_time=None):
#		sql = ("update hit set ")
#		params = []
#		potential_params = (
#				("hit_status",hit_status),
#				("creation_time",_format_datetime(creation_time)),
#				("expiration_time",_format_datetime(expiration_time)),
#				("num_pending",num_pending),
#				("num_available",num_available),
#				("num_completed",num_completed),
#				("max_assignments",max_assignments),
#				("approximate_expiration_time",_format_datetime(approximate_expiration_time)),
#		)
#		usable_params = tuple((pnm,pval) for (pnm,pval) in potential_params if pval is not None)
#		assert len(usable_params) > 0
#		sql += ", ".join("%s=?"%pnm for (pnm,pval) in usable_params)
#		sql += "where hit_id=?;"
#		params = tuple(pval for (pnm,pval) in usable_params) + (hit_id,)
#		self.query(sql, *params)                   # [pylint] tolerate *params magic : pylint:disable=W0142
	

## from update_hits() ... old implementation
#		potential_params = (
#				("hit_status",hit_status),
#				("creation_time",_format_datetime(creation_time) if creation_time is not _UNDEFINED else None),
#				("expiration_time",_format_datetime(expiration_time)),
#				("num_pending",num_pending),
#				("num_available",num_available),
#				("num_completed",num_completed),
#				("max_assignments",max_assignments),
#				("approximate_expiration_time",_format_datetime(approximate_expiration_time)),
#		)
#		usable_params = tuple((pnm,pval) for (pnm,pval) in potential_params if pval is not _UNDEFINED)
#		assert not any(v is None for (k,v) in usable_params if k != "approximate_expiration_time")
#
#		assert len(usable_params) > 0
#		set_parts = []
#		query_params = []
#		for pnm,pval in potential_params:
#			if pval is not _UNDEFINED:
#				if pval is None:
#					assert pnm == "approximate_expiration_time"
#					set_parts.append("%s=NULL")
#				else:
#					set_parts.append( "%s=?" )
#					query_params.append(pval)

#	def _commit_all_connections(self):
#		conns = self._get_all_connections_in_pool()
#		for conn in conns:
#			conn.commit()
#		self._log( "Did DB commit on all %d connection(s) in connection pool"%len(conns) )


