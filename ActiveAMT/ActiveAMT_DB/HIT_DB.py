import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
db_location = './hit_database.db'


class HIT(Base):
    """
    HIT database class

    TABLE INFO:
        __tablename__ = 'HITS'

        id = String, primary_key, the id of the HIT
        type = String [ex. 'txt', 'img']
        template = String [ex. 'basic_textbox.html']
        img_src = String, should be a URL to the image
        question =  String, the question for the HIT
        answer = String, or 'label', the response to the HIT
        completed = Boolean, flag to show HIT completion, useful for querying for remaining HITs
    """

    __tablename__ = "HITs"

    id = Column(String(255), primary_key=True)
    type = Column(String(255))
    template = Column(String(255))
    img_src = Column(String(255))
    question = Column(String(255), nullable=False)
    answer = Column(String(255))
    html = Column(String(255))
    variables = Column(String(255))
    completed = Column(Boolean)


class HITDbHandler(object):
    """
    Class to interface with the HIT database
    """

    def __init__(self):
        """
        Simply check if there is a HIT database in the CWD. If not, make a new one.
        """
        self.db_location = db_location
        if not os.path.exists(self.db_location):
            self.setup_db()

    def setup_db(self):
        """
        Create a new database in the CWD from the HIT class.
        """
        print("\nSetting up database at {}".format(self.db_location))
        engine = create_engine('sqlite:///{}'.format(self.db_location))
        Base.metadata.create_all(bind=engine)

    def add_to_db(self, hit):
        """
        Take in a HIT, map it to a new HIT_DB table entry.
        """
        session = self.connect_to_db()

        task_type = hit['task']['type']

        # These attributes may or may not be keys for each hit.
        # Must check for key then map to variable to prevent explosions.
        img_src = ""
        question = ""
        html = ""
        variables = ""

        if task_type == 'img':
            img_src = hit['task']['img_src']

        if 'question' in hit['task']:
            question = hit['task']['question']
        elif task_type != 'html':
            raise UserWarning("You must provide a question for all 'txt' and 'img' type tasks!")

        if 'html' in hit['task']:
            html = hit['task']['html']

        if 'db_vars' in hit['task']:
            variables = hit['task']['db_vars']

        new_hit = HIT(
                        id=hit['id'],
                        type=task_type,
                        template=hit['task']['template'],
                        img_src=img_src,
                        question=question,
                        answer=hit['answer'],
                        html=html,
                        variables=variables,
                        completed=False
                      )
        session.add(new_hit)
        session.commit()
        print('\tAdded HIT[{0}] to database!'.format(hit['id']))
        session.close()

    def remove_hit_by_id(self, hit_id):
        """
        Take in a HIT id. Remove that HIT.
        """
        session = self.connect_to_db()
        hit_to_remove = session.query(HIT).filter(HIT.id == hit_id).first()
        session.delete(hit_to_remove)
        session.commit()
        session.close()

    def get_hit_by_id(self, hit_id):
        """
        Take in a HIT id. Return that HIT.
        """
        session = self.connect_to_db()
        hit = session.query(HIT).filter(HIT.id == hit_id).first()
        session.close()

        hit = self.db_to_dict(hit)

        return hit

    def get_all_hits(self):
        """
        Return a list of all of the HITs in the database.
        """
        hits = []

        session = self.connect_to_db()
        temp_hits = session.query(HIT).all()
        session.close()

        for hit in temp_hits:

            temp_hit = self.db_to_dict(hit)

            hits.append(temp_hit)

        return hits

    def get_completed_hits(self):
        """
        Return a list of the HITs that have been completed.
        """
        session = self.connect_to_db()
        completed_hits = session.query(HIT).filter(HIT.completed).all()
        session.close()

        hits = []

        for hit in completed_hits:

            temp_hit = self.db_to_dict(hit)
            hits.append(temp_hit)

        return hits

    def get_remaining_hits(self):
        """
        Return a list of the HITs that have yet to be completed.
        """
        session = self.connect_to_db()
        remaining_hits = session.query(HIT).filter(HIT.completed == False).all()
        session.close()

        hits = []

        for hit in remaining_hits:

            temp_hit = self.db_to_dict(hit)
            hits.append(temp_hit)

        return hits

    def set_answer_for_hit(self, hit_id, answer):
        """
        Set the answer for the HIT given by the HIT id provided.
        """
        session = self.connect_to_db()
        hit = session.query(HIT).filter(HIT.id == hit_id).first()
        hit.answer = answer
        hit.completed = True
        session.commit()
        session.close()

    def db_to_dict(self, hit):
        """
        Helper method to map a DB entry to a dict
        """

        # Un-flattens variables, list of dictionaries.
        variables = {}
        kv_pairs = hit.variables.split(',')
        del kv_pairs[-1]  # The string ended with a comma, so the last index is blank.

        for pair in kv_pairs:
            split = pair.split(':')
            key, val = split[0], split[1]

            variables[key] = val

        temp_hit = {
            'id': str(hit.id),
            'type': str(hit.type),
            'template': str(hit.template),
            'img_src': str(hit.img_src),
            'question': str(hit.question),
            'answer': str(hit.answer),
            'html': str(hit.html),
            'variables': variables,
            'completed': bool(hit.completed)
        }

        return temp_hit

    def connect_to_db(self):
        """
        Helper function that makes a connection to the HIT database and returns the connection.
        """
        engine = create_engine('sqlite:///{}'.format(self.db_location))
        Base.metadata.bind = engine
        DBSession = sessionmaker()
        DBSession.bind = engine
        session = DBSession()

        return session
