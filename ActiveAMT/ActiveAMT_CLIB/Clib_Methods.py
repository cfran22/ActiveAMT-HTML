import copy
import glob
import os
import shutil

import crowdlib as cl
import crowdlib_settings as cls
from ActiveAMT.ActiveAMT_DB import HITDbHandler
from ActiveAMT.ActiveAMT_FLASK import server_location, template_map, custom_hit_path


class Clib(object):

    def __init__(self):
        self.db = HITDbHandler()
        self.custom_hit_path = custom_hit_path
        self.server = server_location

    def _create_hittype(self, hit_type_init_file=None):
        """
        Creates the HIT_Type from the HIT_Type initialization file
        """

        hif = hit_type_init_file

        if not hif or not os.path.exists(hif):
            raise UserWarning("Please provide a valid HITType initialization file!")

        print('\nCreating HITType from {}'.format(hif))

        hit_type_info = cls.default_hittype

        hif = open(hif)
        # Set all available keys from the HIT_Type initialization file
        for line in hif:
            key_val_pair = line.split(':')
            key, val = key_val_pair[0], key_val_pair[1].split('\n')[0]
            hit_type_info[key] = val
        hif.close()

        hit_type = cl.create_hit_type(
            title=(hit_type_info["title"]),
            description=hit_type_info["description"],
            reward=float(hit_type_info["reward"]),
            time_limit=self._eqval(hit_type_info["time_limit"]),
            keywords=hit_type_info["keywords"].split(','),
            qualification_requirements=hit_type_info["qualification_requirements"],
            autopay_delay=self._eqval(hit_type_info["autopay_delay"])
        )

        return hit_type

    def _make_hit(self, task, hit_type):
        """
        Creates a HIT for the given task and sends it to the HIT database.
        """

        hit = hit_type.create_hit("{}{}".format(self.server, task['template']), 650)

        print("\n\t****Generated HIT: {}****".format(hit.id))

        hit_for_db = {
            'id': hit.id,
            'task': task,
            'answer': ""
        }

        self.db.add_to_db(hit_for_db)

    def _eqval(self, str_val):
        """
        Simple helper method to evaluate multiplication strings.
        """
        if isinstance(str_val, basestring):

            operands = str_val.split('*')
            val = 1

            for operand in operands:
                val *= int(operand)

            return val

        else:
            return str_val

    def _handle_html_task(self, task):
        """
        Method to handle custom HTML tasks.

        Does not manipulate any of the task attributes.
        Simply makes sure the task is valid and gets the necessary HTML into the correct flask path.
        Also flattens variables dict into a string to store in the db.
        """

        # If the user provided a desired filename, use the filename for the new flask template file
        if 'fname' in task:
            if not task['fname'].endswith('.html'):
                task['fname'] = task['fname'].split('.')[0]
                task['fname'] += '.html'
            task['html'] = task['fname']

        # Check if the user is providing an HTML file with the 'path' key
        if 'path' in task:
            # Check if the file path they provided is a valid file path
            if os.path.exists(task['path']):
                # Use the desired filename if it was provided
                if 'fname' in task:
                    shutil.copy(task['path'], (self.custom_hit_path + '/' + task['html']))
                # If a desired filename was not provided, just use the existing filename
                else:
                    shutil.copy(task['path'], (self.custom_hit_path + '/' + task['path'].split('/')[-1]))
                    task['html'] = task['path'].split('/')[-1]  # Should be just the filename.html
            else:
                raise UserWarning("{} does not exist!".format(task['path']))
        # If the user does not provide an HTML file, they must provide raw HTML
        elif 'raw' in task:
            # If the user doesn't have a desired filename, name the new file custom_hit#, where the number is sequential
            if 'fname' not in task:
                cur_custom_hits = glob.glob1(self.custom_hit_path, 'custom_hit*.html')
                num_custom_hits = len(cur_custom_hits) + 1
                new_custom_hit = open(self.custom_hit_path + '/custom_hit{}.html'.format(num_custom_hits), 'w')
                new_custom_hit.write(task['raw'])
                new_custom_hit.close()
                task['html'] = 'custom_hit{}.html'.format(num_custom_hits)
            # Otherwise, use the desired filename
            else:
                new_custom_hit = open((self.custom_hit_path + '/' + task['fname']), 'w')
                new_custom_hit.write(task['raw'])
                new_custom_hit.close()
        else:
            raise KeyError("You must provide either a path to your HTML file with the 'path' key or the raw HTML "
                           "with the 'raw' key!")

        flat_dict = ""

        if 'variables' in task:

            if not type(task['variables']) is dict:
                raise KeyError("'variables' must be a dict of key-val pairs, each being a variable to be injected into "
                               "the HTML.")

            task['db_vars'] = copy.deepcopy(task['variables'])

            for key, value in task['db_vars'].iteritems():
                flat_dict += "{}:{},".format(key, value)

            task['db_vars'] = flat_dict

        return task

    def create_hits(self, tasks, hit_type_init_file=None):
        """
        Combines the methods from above to generate a HIT for each task
        """

        # Must create the HITType in order to create a HIT
        hit_type = self._create_hittype(hit_type_init_file)

        # Go through each task in the list of tasks
        for task in tasks:

            # Handle the custom HTML tasks
            if task['type'] == 'html':
                task = self._handle_html_task(task)

            task['template'] = template_map[task['type']]
            self._make_hit(task, hit_type)
