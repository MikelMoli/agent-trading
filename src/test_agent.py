import os

import pandas as pd

from environments.single_asset_trading_environment import SingleAssetTradingEnvironment
from agent.agent import Agent

if __name__ == "__main__":
    df = pd.read_csv("../data/merged/complete_data.csv")[["date", "open", "high", "close", "low", "volume"]]
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"].dt.hour % 1 == 0) & (df["date"].dt.minute == 0)]
    df.to_csv("../data/merged/complete_data_1H.csv", index=False)

    data_path = os.path.abspath("../data/merged/complete_data_1H.csv")
    initial_account_balance = 10000
    reward_window = 24
    reward_method = "simple-profit"
    unavailable_action_penalization_reward = -1

    env_config = {
        "data_path": data_path,
        "initial_account_balance": initial_account_balance,
        "reward_window": reward_window,
        "reward_method": reward_method,
        "unavailable_action_penalization_reward": unavailable_action_penalization_reward
    }

    env = SingleAssetTradingEnvironment(env_config)
    agent = Agent("PPO", "MlpPolicy", env)

    print("TRAINING...")
    agent.train(total_timesteps=150_000)
    print("EVALUATING...")
    agent.evaluate(n_eval_episodes=1)
    print("EXECUTING...")
    agent.execute(render_mode="human")