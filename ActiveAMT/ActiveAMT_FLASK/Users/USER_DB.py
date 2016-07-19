import os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
db_location = os.getcwd().split('ActiveAMT/')[0] + '/ActiveAMT/ActiveAMT_FLASK/Users/users.db'


class User(Base):
    """
    USER database class

    TABLE INFO:
        __tablename__ = 'USERS'

        id = String, username, primary_key
        password = String, user's password, non-nullable
        admin = Boolean, shows if the user is an admin
    """

    __tablename__ = 'USERS'

    id = Column(String(255), primary_key=True)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean)


class UserDbHandler(object):
    """
    Class to interface with the USER database.
    """

    def __init__(self):
        self.db_location = db_location
        if not os.path.exists(self.db_location):
            self.setup_db()

    def setup_db(self):
        """
        Creates a new USER database in the CWD.
        """
        engine = create_engine('sqlite:///{}'.format(self.db_location))
        Base.metadata.create_all(bind=engine)

    def add_user(self, username, pword, is_admin=False):
        """
        Adds a user to the USER database.
        """
        session = self.connect_to_db()

        new_user = User(
            id=username,
            password=pword,
            is_admin=is_admin
        )

        session.add(new_user)
        session.commit()
        session.close()

    def del_user(self, username):
        """
        Deletes a user, by username, from the USER database.
        """
        session = self.connect_to_db()

        user = session.query(User).filter(User.id == username).first()
        session.delete(user)
        session.commit()

        session.close()

    def get_user_by_username(self, username):
        """
        Gets a specific user, by username, from the USER database.
        """
        session = self.connect_to_db()
        user = session.query(User).filter(User.id == username).first()
        session.close()

        return user

    def get_all_users(self):
        """
        Gets every user from the USER database, as a list of dicts.
        """

        user_list = []

        session = self.connect_to_db()

        users = session.query(User).all()

        for user in users:
            temp_user = {
                'id': str(user.id),
                'password': str(user.password),
                'is_admin': str(user.is_admin).capitalize()
            }
            user_list.append(temp_user)

        session.close()

        return user_list

    def login(self, req_user):
        """
        Checks a user's credentials. Returns the user.
        """
        is_user_valid = False
        is_admin = False
        username = None
        password = None
        login_error = {
            'is_error': True,
            'error_message': "Username and password do not match!"
        }

        """  Try to get the requested user from the database """
        session = self.connect_to_db()
        user = session.query(User).filter(User.id == req_user['username']).first()
        session.close()

        if user:
            """ user exists """
            username = user.id
            if req_user['password'] == user.password:
                is_user_valid = True
                is_admin = user.is_admin
                password = True
            else:
                password = False

        user = {
            'is_user_valid': is_user_valid,
            'is_admin': is_admin,
            'username': username,
            'password': password,
            'login_error': login_error
        }

        return user

    def update_user(self, old_username, new_username, new_password, new_is_admin):
        """
        Replaces the existing user's credentials with the new parameters.
        """
        session = self.connect_to_db()
        user = session.query(User).filter(User.id == old_username).first()
        user.id = new_username
        user.password = new_password
        user.is_admin = new_is_admin
        session.commit()
        session.close()

    def connect_to_db(self):
        """
        Helper function that makes a connection to the USER database and returns the connection.
        """
        engine = create_engine('sqlite:///{}'.format(self.db_location))
        Base.metadata.bind = engine
        DBSession = sessionmaker()
        DBSession.bind = engine
        session = DBSession()

        return session
