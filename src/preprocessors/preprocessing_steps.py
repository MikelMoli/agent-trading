import pandas as pd

from typing import List
from preprocessor import Preprocessor

class PreprocessingSteps:
    def __init__(self, steps: List[Preprocessor]):
        self.steps = steps
    
    def preprocess(self, df) -> pd.DataFrame:
        for preprocessing_step in self.steps:
            df = preprocessing_step.preprocess(df)
        
        return df
