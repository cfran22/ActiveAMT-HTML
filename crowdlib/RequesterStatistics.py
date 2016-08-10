# vim: set fileencoding=utf-8 noexpandtab:
	#
# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alexander J. Quinn
@contact: aq@purdue.edu
@since: November 2010
'''

from __future__ import division, with_statement

# pylint: disable=W0212
#         Allow lambda functions to access protected method _get_statistic
# pylint: disable=R0903
#         Don't complain about too few public methods.

class RequesterStatistics(object):
	def __init__(self, get_amt_fn, time_period):
		assert time_period in ("OneDay", "SevenDays", "ThirtyDays", "LifeToDate")

		self._time_period = time_period
		self._get_amt_fn = get_amt_fn
	
	def _get_statistic(self, statistic):
		return self._get_amt_fn().get_requester_statistic(statistic=statistic, time_period=self._time_period)

	number_assignments_available = property(lambda self: self._get_statistic("NumberAssignmentsAvailable"))

	number_assignments_accepted = property(lambda self: self._get_statistic("NumberAssignmentsAccepted"))

	number_assignments_pending = property(lambda self: self._get_statistic("NumberAssignmentsPending"))

	number_assignments_approved = property(lambda self: self._get_statistic("NumberAssignmentsApproved"))

	number_assignments_rejected = property(lambda self: self._get_statistic("NumberAssignmentsRejected"))

	number_assignments_returned = property(lambda self: self._get_statistic("NumberAssignmentsReturned"))

	number_assignments_abandoned = property(lambda self: self._get_statistic("NumberAssignmentsAbandoned"))

	percent_assignments_approved = property(lambda self: self._get_statistic("PercentAssignmentsApproved"))

	percent_assignments_rejected = property(lambda self: self._get_statistic("PercentAssignmentsRejected"))

	total_reward_payout = property(lambda self: self._get_statistic("TotalRewardPayout"))

	average_reward_amount = property(lambda self: self._get_statistic("AverageRewardAmount"))

	total_reward_fee_payout = property(lambda self: self._get_statistic("TotalRewardFeePayout"))

	total_fee_payout = property(lambda self: self._get_statistic("TotalFeePayout"))

	total_reward_and_fee_payout = property(lambda self: self._get_statistic("TotalRewardAndFeePayout"))

	total_bonus_payout = property(lambda self: self._get_statistic("TotalBonusPayout"))

	total_bonus_fee_payout = property(lambda self: self._get_statistic("TotalBonusFeePayout"))

	number_hits_created = property(lambda self: self._get_statistic("NumberHITsCreated"))

	number_hits_completed = property(lambda self: self._get_statistic("NumberHITsCompleted"))

	number_hits_assignable_last_night = property(lambda self: self._get_statistic("NumberHITsAssignable"))

	number_hits_reviewable = property(lambda self: self._get_statistic("NumberHITsReviewable"))

	estimated_reward_liability = property(lambda self: self._get_statistic("EstimatedRewardLiability"))

	estimated_fee_liability = property(lambda self: self._get_statistic("EstimatedFeeLiability"))

	estimated_total_liability = property(lambda self: self._get_statistic("EstimatedTotalLiability"))
