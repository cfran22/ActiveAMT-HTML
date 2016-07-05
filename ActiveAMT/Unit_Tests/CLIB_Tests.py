from ActiveAMT.ActiveAMT_CLIB import Clib
from ActiveAMT.ActiveAMT_DB import hit_db_location
import os


class CLIBTests(object):
    """
    Everything necessary to test the functionality of the crowdlib logic.
    """

    def __init__(self):
        print("\n****Running Clib tests...")
        self.clib = Clib()

    def eqval_evaluates_correctly(self):
        """
        Test if the eqval method evaluates multiplication strings correctly.
        """
        passed = "FAIL "
        mult_str = "2*3*4"
        expected = 24

        if self.clib._eqval(mult_str) == expected:
            passed = "PASS "

        print("Eqval - {}".format(passed))

    def init_hittype_correctly(self):
        """
        Test if the HITType gets created correctly.
        """
        import datetime

        passed = "FAIL "

        hit_type = self.clib._create_hittype('./MockHITType.init')

        if hit_type.title == 'Init Test' and hit_type.description == 'Testing, testing.' and \
           hit_type.keywords == ['Test', 'Mock'] and hit_type.reward == 1.23 and \
           hit_type.time_limit == datetime.timedelta(0, 3600):
            passed = "PASS "

        print("Init HITType - {}".format(passed))

    def cleanup(self):
        """
        Method to run after all tests.
        """
        os.remove(hit_db_location)
        print("\nRemoving database...")

    def run_all(self):
        """
        Method to simply run all available tests in one shot.
        """
        self.eqval_evaluates_correctly()
        self.init_hittype_correctly()
        self.cleanup()

