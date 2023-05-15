import sys
import gym

sys.path.insert(1, "..") 

from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.evaluation import evaluate_policy

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
        
    def train(self, total_timesteps: int) -> None:
        self.model.learn(total_timesteps=total_timesteps)

    def evaluate(self, n_eval_episodes: int) -> None:
        mean_reward, std_reward = evaluate_policy(self.model, self.model.get_env(), n_eval_episodes=n_eval_episodes)
        print(f"MEAN REWARD {mean_reward} | STD REWARD {std_reward}")

    def execute(self, render_mode: str) -> None:
        i = 0
        vec_env = self.model.get_env()
        obs = vec_env.reset()
        while True:
            action, _states = self.model.predict(obs, deterministic=True)
            obs, rewards, done, info = vec_env.step(action)

            if done:
                break

            if i % 100 == 0:
                vec_env.render(render_mode)

            i += 1