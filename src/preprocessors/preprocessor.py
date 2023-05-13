import abc

import pandas as pd

class Preprocessor(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def preprocess(self, df: pd.DataFrame):
        pass
