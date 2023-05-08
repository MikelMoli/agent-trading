import abc

class Reward(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def calculate_reward(self):
        pass
