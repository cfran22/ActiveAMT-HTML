# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: April 2011
'''

from __future__ import division, with_statement

from collections import namedtuple
BonusRecord = namedtuple("BonusRecord", ("assignment_id", "worker_id", "amount", "currency", "payment_time", "reason"))
