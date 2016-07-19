# Imported to determine if files are created/destroyed correctly
import os

from ActiveAMT.ActiveAMT_DB import HITDbHandler


class DBTests(object):
    """
    Everything necessary to test the functionality of the HIT database
    """

    def __init__(self):
        if os.path.exists('./hit_database.db'):
            os.remove('./hit_database.db')
        print('\n****Running database tests...\n')
        self.test_db = HITDbHandler()

    def creates_db_correctly(self):
        """
        Check to see if we can create a HIT database correctly.
        """

        if os.path.exists(self.test_db.db_location):
            print('Database Creation - PASS')
        else:
            print('Database Creation -  Failed')

    def adds_to_db_gets_from_db_correctly(self):
        """
        Check to see if we can add HITs to the HIT database correctly
        """

        add_to_passed = True
        add_to_reason = ""
        get_from_passed = True
        get_from_reason = ""

        mock_hit = {

            'id': '1234TEST5678',
            'task': {
                'type': 'img',
                'question': 'Do you see a dog in this picture?',
                'img_src': 'http://i.imgur.com/iY8WB3H.jpg',
                'template': 'basic_image.html'
            },
            'answer': 'Yes'
        }

        junk_hit = {

            'id': 'KX1GH098BKLLX',
            'task': {
                'type': 'txt',
                'question': 'Why so serious?',
                'img_src': '',
                'template': 'basic_textbox.html'
            },
            'answer': "I'm Batman"
        }

        self.test_db.add_to_db(mock_hit)
        self.test_db.add_to_db(junk_hit)

        returned_hit = self.test_db.get_hit_by_id(mock_hit['id'])

        if returned_hit is None:
            add_to_passed = False
            add_to_reason = "HIT returned from DB is None"
        else:
            for key in mock_hit.keys():
                if mock_hit[key] != returned_hit[key]:
                    get_from_passed = False
                    get_from_reason = "Key[{0}] did not match between the mock hit and DB entry".format(key)
                    break

        if add_to_passed:
            print("Add HIT to DB - PASS")
        else:
            print("Add HIT to DB - FAIL: {0}".format(add_to_reason))

        if get_from_passed:
            print("Get HIT from DB - PASS")
        else:
            print("Get HIT from DB - FAIL: {0}".format(get_from_reason))

    def sets_answer_correctly(self):
        """
        Checks if we are able to set the answer for a HIT, by id, correctly.
        """

        self.test_db.set_answer_for_hit('1234TEST5678', 'New answer')

        if self.test_db.get_hit_by_id('1234TEST5678')['answer'] == 'New answer':
            print('Set Answer - PASS')
        else:
            print('Set Answer - FAIL')

    def gets_correct_hits_remaining(self):
        """
        Checks to see if we are able to get the correct number of remaining HITs.
        """

        if len(self.test_db.get_remaining_hits()) == 1:
            print('Get Remaining HITs - PASS')
        else:
            print('Get Remaining HITs - FAIL')

    def gets_completed_hits_correctly(self):
        """
        Checks to see if we are able to get the correct number of completed HITs.
        """

        if len(self.test_db.get_completed_hits()) == 1:
            print('Get Completed HITs - PASS')
        else:
            print('Get Completed HITs - FAIL')

    def removes_hit_correctly(self):
        """
        Checks to see if we are able to remove a HIT, by id, correctly.
        """

        self.test_db.remove_hit_by_id('1234TEST5678')

        if not self.test_db.get_hit_by_id('1234TEST5678'):
            print('Remove HIT - PASS')
        else:
            print('Remove HIT - FAIL')

    def cleanup(self):
        """
        Clean up code to be run at the end of all tests.
        """
        print('\nRemoving database...')
        os.remove(self.test_db.db_location)

    def run_all(self):
        """
        Method to simply run all available database tests in one shot.
        """
        self.creates_db_correctly()
        self.adds_to_db_gets_from_db_correctly()
        self.sets_answer_correctly()
        self.gets_correct_hits_remaining()
        self.gets_completed_hits_correctly()
        self.removes_hit_correctly()
        self.cleanup()

