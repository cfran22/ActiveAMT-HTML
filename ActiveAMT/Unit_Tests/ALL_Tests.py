from ActiveAMT.Unit_Tests import CLIBTests, DBTests


def run_all():
    """
    Simple method call to run all tests from all modules.
    """
    DBTests().run_all()
    CLIBTests().run_all()

run_all()
