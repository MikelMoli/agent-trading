import os
import sys
import gymnasium as gym

import pandas as pd

sys.path.insert(1, "..") 

from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.evaluation import evaluate_policy

from environments.single_asset_trading_environment import SingleAssetTradingEnvironment

class Agent:
    def __init__(self, algorithm: str, policy: str, environment: gym.Env):
        self.algorithm = algorithm
        self.policy = policy
        self.environment = environment
        self.model = self.create_model()

    def create_model(self):
        if self.algorithm == "A2C":
            return A2C(self.policy, self.environment, verbose=1)
        elif self.algorithm == "PPO":
            return PPO(self.policy, self.environment, verbose=1)
        elif self.algorithm == "DQN":
            return DQN(self.policy, self.environment, verbose=1)
        else:
            raise NotImplementedError(f"{self.algorithm} not supported.")
        
    def train(self):
        self.model.learn(total_timesteps=10000)

    def evaluate(self):
        mean_reward, std_reward = evaluate_policy(self.model, self.model.get_env(), n_eval_episodes=1)
        print(f"MEAN REWARD {mean_reward} | STD REWARD {std_reward}")

    def execute(self):
        vec_env = self.model.get_env()
        obs = vec_env.reset()
        for i in range(1000):
            action, _states = self.model.predict(obs, deterministic=True)
            obs, rewards, done, info = vec_env.step(action)
            print(info)

            if done:
                break

            if i % 100 == 0:
                vec_env.render("human")

if __name__ == "__main__":
    df = pd.read_csv("../../data/merged/cleaned_1_H_merged_data.csv")[["open", "high", "close", "low"]]

    data_path = os.path.abspath("../../data/merged/cleaned_1_H_merged_data.csv")
    initial_account_balance = 10000
    reward_window = 24
    reward_method = "simple-profit"
    render_mode = "console"
    unavailable_action_penalization_reward = -1
    epochs = 1
    episodes_per_epoch = df.shape[0] - 1

    env_config = {
        "data_path": data_path,
        "initial_account_balance": initial_account_balance,
        "reward_window": reward_window,
        "reward_method": reward_method,
        "unavailable_action_penalization_reward": unavailable_action_penalization_reward
    }

    env = SingleAssetTradingEnvironment(env_config)
    agent = Agent("A2C", "MlpPolicy", env)

    print("TRAINING...")
    agent.train()
    print("EVALUATING...")
    agent.evaluate()
    print("EXECUTING...")
    agent.execute()