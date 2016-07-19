import logging
import threading
import time

from ActiveAMT_CLIB import Clib
from ActiveAMT_EVENTS.observable import Observable
from ActiveAMT_FLASK import app, ssl_ctx

building_HTML = True
debugging = False
_flask_running = False


class ActiveAMT(object):
    """
    Class to provide the whole ActiveAMT functionality
    """

    def __init__(self):
        self._flask_thread = _FlaskThread()
        self._observable = Observable()
        if not debugging:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
        self.clib = Clib()

    def init_tasks(self, tasks, hit_type_init_file=None):
        """
        Takes a list of tasks and turns them into HITs on AMT.
        """
        if not type(tasks) is list:
            # If only a single, non-list held task was passed in, add it to a list
            temp_list = [tasks]
            tasks = temp_list
            del temp_list

        if len(tasks) == 0:
            raise RuntimeError("You must pass at least one task to init_tasks!")
        else:
            global _flask_running
            if not _flask_running:  # Only allow one Flask server to be running
                self._flask_thread.start()
            time.sleep(1)  # Here simply to clean up console output
            if not building_HTML:
                self.clib.create_hits(tasks, hit_type_init_file)

    def register_observer(self, observer):
        """
        Adds an observer to the observer list of the class instances observer class instance.
        """
        with self._observable.lock:
            self._observable.register(observer)


class _FlaskThread(threading.Thread):
    """
    Thread class for the Flask server.
    """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        """
        Code that runs when a Flask thread is started.
        """
        global _flask_running
        _flask_running = True
        print("\nA Flask server has been spawned on {}".format(self.name))
        app.run(debug=True, ssl_context=ssl_ctx, use_reloader=False, host='0.0.0.0', threaded=True)
