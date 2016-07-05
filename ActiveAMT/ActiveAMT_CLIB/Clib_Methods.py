import os
import crowdlib as cl
import crowdlib_settings as cls
from ActiveAMT.ActiveAMT_DB import HITDbHandler
from ActiveAMT.ActiveAMT_FLASK import server_location, template_map


class Clib(object):

    def __init__(self):
        self.db = HITDbHandler()
        self.server = server_location

    def _create_hittype(self, hit_type_init_file=None):
        """
        Creates the HIT_Type from the HIT_Type initialization file
        """

        hif = hit_type_init_file

        if not hif or not os.path.exists(hif):
            raise UserWarning("\Please provide a valid HITType initialization file!")

        print('\nCreating HITType from {}'.format(hif))

        hit_type_info = cls.default_hittype

        if os.path.exists(hif):
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

        hit = hit_type.create_hit("{}{}".format(self.server, task['template']), 450)

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

    def create_hits(self, tasks, hit_type_init_file=None):
        """
        Combines the methods from above to generate a HIT for each task
        """
        hit_type = self._create_hittype(hit_type_init_file)

        for task in tasks:
            task['template'] = template_map[task['type']]
            self._make_hit(task, hit_type)
