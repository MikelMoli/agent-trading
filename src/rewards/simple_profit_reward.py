from typing import List

from rewards.reward import Reward

class SimpleProfitReward(Reward):
    def __init__(self, window: int):
        super().__init__()
        self.window = window

    def calculate_reward(self, account_balance_history: List[float]) -> float:
        current_account_balance = account_balance_history[-1]
        min_account_balance_in_window = account_balance_history[-min(len(account_balance_history), self.window)]
        
        return current_account_balance / min_account_balance_in_window - 1.0