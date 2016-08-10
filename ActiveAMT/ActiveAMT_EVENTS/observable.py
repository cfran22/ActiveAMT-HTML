import threading


class Observable(object):

    observers = []
    lock = threading.Lock()

    def __init__(self):
        pass

    def register(self, observer):
        """
        Registers an observer to be notified of events.
        """
        if observer not in self.observers:
            self.observers.append(observer)

    def unregister(self, observer):
        """
        Unregisters an observer to be notified of events.
        """
        if observer in self.observers:
            self.observers.remove(observer)

    def unregister_all(self):
        """
        Unregisters all observers to be notified of events.
        """
        self.observers = []

    def notify_observers(self, *args, **kwargs):
        """
        Notifies all of the observers when an event happens.
        """
        for observer in self.observers:
            observer.update(*args, **kwargs)
