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
    completed = Column(Boolean)


class HITDbHandler(object):
    """
    Class to interface with the HIT database
    """

    def __init__(self):
        """
        Simply check if there is a HIT database in the CWD. If so, delete it to start fresh.
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
        img_src = ""
        if task_type == 'img':
            img_src = hit['task']['img_src']
        question = hit['task']['question']

        new_hit = HIT(
                        id=hit['id'],
                        type=task_type,
                        template=hit['task']['template'],
                        img_src=img_src,
                        question=question,
                        answer=hit['answer'],
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
        hit_to_remove = self.get_hit_by_id(hit_id)
        session = self.connect_to_db()
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

        return hit

    def get_completed_hits(self):
        """
        Return a list of the HITs that have been completed.
        """
        session = self.connect_to_db()
        completed_hits = session.query(HIT).filter(HIT.completed).all()
        session.close()

        return completed_hits

    def get_remaining_hits(self):
        """
        Return a list of the HITs that have yet to be completed.
        """
        session = self.connect_to_db()
        remaining_hits = session.query(HIT).filter(HIT.completed == False).all()
        session.close()

        return remaining_hits

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

    def remove_db(self):
        """
        Simple method to remove the HIT database in the CWD
        """
        if os.path.exists(self.db_location):
            os.remove(self.db_location)
            print("\nRemoving database...")

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
