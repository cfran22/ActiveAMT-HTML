import time
import logging
import threading
from ActiveAMT_FLASK import app, ssl_ctx
from ActiveAMT_CLIB import Clib

building_HTML = True
_flask_running = False


class ActiveAMT(object):
    """
    Class to provide the whole ActiveAMT functionality
    """

    def __init__(self):
        self._flask_thread = _FlaskThread()
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.clib = Clib()

    def init_tasks(self, tasks, hit_type_init_file=None):
        """
        Takes a list of tasks and turns them into HITs on AMT.
        """
        if len(tasks) == 0:
            raise RuntimeError("You must pass at least one task to init_tasks!")
        else:
            global _flask_running
            if not _flask_running:  # Only allow one Flask server to be running
                self._flask_thread.start()
            time.sleep(1)  # Here simply to clean up console output
            if not building_HTML:
                self.clib.create_hits(tasks, hit_type_init_file)

    # TODO: Implement a method to notify the caller when all tasks are completed, returning the labels
    def update_tasks(self):
        pass


class _FlaskThread(threading.Thread):
    """
    Thread class for the Flask server.

    Allows us to run the Flask server on its own thread
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
        app.run(debug=True, ssl_context=ssl_ctx, use_reloader=False)
