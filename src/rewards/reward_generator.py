from typing import List

from rewards.simple_profit_reward import SimpleProfitReward

class RewardGenerator:
    def __init__(self, reward_method: str, reward_window: int):
        self.reward_method = reward_method
        self.reward_window = reward_window

        self.reward_generator = self._initialize_reward_method()

    def _initialize_reward_method(self) -> object:
        if self.reward_method == "simple-profit":
            return SimpleProfitReward(self.reward_window)
        else:
            raise NotImplementedError(f"{self.reward_method} reward method not supported.")
    
    def calculate_reward(self, account_balance_history: List[float]) -> float:
        return self.reward_generator.calculate_reward(account_balance_history)
