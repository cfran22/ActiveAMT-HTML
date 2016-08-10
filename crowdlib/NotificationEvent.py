# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: July 2010

'''

from __future__ import division, with_statement

class NotificationEvent(object):
	def __init__(self, event_type, event_time, hit_type, hit, assignment=None):
		self.event_type = event_type
		self.event_time = event_time
		self.hit_type = hit_type
		self.hit = hit
		self.assignment = assignment