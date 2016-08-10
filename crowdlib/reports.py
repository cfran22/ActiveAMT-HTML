# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: July 22, 2011
'''

from __future__ import division, with_statement

_ACCEPTABLE_FORMATS = ("html", "excel")

def assignment_report(assignments, omit_columns=(), format="excel"):
	from crowdlib.utility.tables import Table
	from crowdlib.utility import total_seconds

	if format not in _ACCEPTABLE_FORMATS:
		raise ValueError("Unexpected table format:  %s (should have been one of %s)"%(format, ", ".join(_ACCEPTABLE_FORMATS)))

	excel_date_format = "%m/%d/%Y %H:%M:%S"
	currency_format = "$%.02f"
	currency_or_empty_if_zero = lambda n:(currency_format%n if n is not None and n!=0 else "")
	datetime_or_empty_if_none = lambda dt:(dt.strftime(excel_date_format) if dt is not None else "")
	#seconds_or_empty_if_none = lambda dt:(dt.strftime(excel_date_format) if dt is not None else "")
	fields = [
			( "Assignment ID", lambda a:a.id ),
			( "Worker ID", lambda a:a.worker.id ),
			( "Accept Time", lambda a:datetime_or_empty_if_none(a.accept_time) ),
			( "Submit Time", lambda a:datetime_or_empty_if_none(a.submit_time) ),
			( "Assignment Status", lambda a:a.assignment_status ),
			( "Review Time", lambda a:datetime_or_empty_if_none(a.review_time) ),
			( "Reward Paid", lambda a:(currency_format%(a.hit.hit_type.reward) if a.is_paid else "") ),
			( "Bonuses Paid", lambda a:currency_or_empty_if_zero(a.bonuses_paid_total_amount) ),
			( "Time Spent (secs)", lambda a:"%d"%(total_seconds(a.time_spent)) ),
			( "Hourly Rate", lambda a:currency_format%(a.hourly_rate) ),
			( "HIT ID", lambda a:a.hit.id ),
			( "HIT Type ID", lambda a:a.hit.hit_type.id ),
			( "Title", lambda a:a.hit.hit_type.title ),
			( "Reward Offered", lambda a:currency_format%(a.hit.hit_type.reward) ),
	]

	row_details = []
	question_ids = []
	for asg in assignments:
		main_vals = []
		for field_name,get_fn in fields: # [pylint] field_name not used : pylint:disable=W0612
			val = get_fn(asg)
			main_vals.append(val)

		answer_strs = {}
		for answer in asg.answers:
			question_id = answer.question_id
			answer_strs[question_id] = answer.text
			if question_id not in question_ids:
				question_ids.append(question_id)

		row_details.append((main_vals, answer_strs))

	headers = [f[0] for f in fields] + question_ids

	rows = []
	for main_vals,answer_strs in row_details:
		row = list(main_vals)
		for question_id in question_ids:
			answer_text = answer_strs.get(question_id,"")
			row.append(answer_text)
		assert len(row)==len(headers), (len(row), len(headers), repr(row), repr(headers))
		rows.append(row)


	col_nums_to_omit = []
	for column in omit_columns:
		if isinstance(column, int):
			if column < len(headers):
				col_nums_to_omit.append(column)
			else:
				raise ValueError("%d is not a valid column index."%column)
		elif isinstance(column, str):
			try:
				col_num = headers.index(column)
			except ValueError:
				raise ValueError("%s is not a valid column header."%(repr(column)))
			col_nums_to_omit.append(col_num)

	col_nums_to_omit.sort(reverse=True)
	table_col_specs = [(header,str) for header in headers]

	for col_num in col_nums_to_omit:
		del table_col_specs[col_num]
	table = Table(*table_col_specs)
	for row in rows:
		for col_num in col_nums_to_omit:
			del row[col_num]
		table.add_row(*row)

	if format=="excel":
		return table.render_tab_delimited()
	elif format=="html":
		return table.render_html()
	else:
		assert False, "Unexpected table format %s, should have been caught earlier."%(repr(format))
