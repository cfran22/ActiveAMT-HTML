from abc import ABCMeta, abstractmethod


class Observer(object):
    """
    Observer interface for the calling code to implement.

    Allows the calling code to register itself for events that ActiveAMT may produce.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        """
        Uniformly named method that will be called on each observer when
        the observable has to update observers on events.
        """
        pass
