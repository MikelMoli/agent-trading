import abc

class Action(metaclass=abc.ABCMeta):
    def __init__(self, trade_commission):
        self.trade_commission = trade_commission
        
    @abc.abstractmethod
    def take_action(self):
        pass
