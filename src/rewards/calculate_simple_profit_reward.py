from typing import List

#calculates the profit made by the agent decisions in the last N steps
def calculate_simple_profit_reward(account_balance_history: List[float], window: int) -> float:
    current_account_balance = account_balance_history[-1]
    min_account_balance_in_window = account_balance_history[-min(len(account_balance_history), window)]
        
    return current_account_balance / min_account_balance_in_window - 1.0