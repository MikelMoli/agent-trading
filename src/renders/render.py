import abc

class Render(metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    @abc.abstractmethod
    def render(self):
        pass
