# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: May 2010

Class to manage global settings.  This class should not be used directly.
Instead, CrowdLib has a "settings" member which is the singleton instance of
this class.  Use that to modify settings like this:

	crowdlib.settings.service_type = "sandbox"

The reason this is a class instead of just variables in a module is that in the
future I anticipate making these into properties with some checking to make
sure the values make sense.
'''

from __future__ import division, with_statement

class CrowdLibSettings(object):
	# For now, these are all public members, not properties, since no access control is needed.

	def __init__(self):
		import os
		default_db_dir = os.path.abspath(os.path.expanduser("~/.crowdlib_data/"))

		self.service_type = None     ### TODO - REQUIRED ###
		self.db_dir = default_db_dir ### TODO - REQUIRED ###
		self.aws_account_id = None   ### TODO - REQUIRED ###
		self.aws_account_key = None  ### TODO - REQUIRED ###

		self.default_reward = None   ### TODO ###
		self.default_autopay_delay = 60*60*24*7 # 7 days
		self.default_currency = "USD" # undocumented because it must always be "USD"
		self.default_lifetime = 60*60*24*7  # 7 days
		self.default_max_assignments = 1
		self.default_time_limit = 60*30 # 30 minutes
		self.default_qualification_requirements = () # Default:  none
		self.default_keywords = ()

	# CrowdLibSettings is a SINGLETON class
	#
	# Credit: "jojo" on StackOverflow, 11/27/2009
	# http://stackoverflow.com/questions/42558/python-and-the-singleton-pattern
	_singleton_instance = None
	def __new__(cls, *args, **kwargs):
		if cls._singleton_instance is None:
			cls._singleton_instance = super(CrowdLibSettings, cls).__new__(cls, *args, **kwargs)
		return cls._singleton_instance
