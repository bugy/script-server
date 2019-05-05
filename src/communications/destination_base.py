import abc


class Destination(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def send(self, title, body, files=None):
        pass
