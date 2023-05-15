import gym
import pandas as pd
import numpy as np

from typing import Tuple, List
from rewards.reward_generator import RewardGenerator
from actions.single_asset_discrete_full_action import SingleAssetDiscreteFullAction
from renders.single_asset_renderer import SingleAssetRenderer
from utils.single_asset_trading_utils import get_position_name, get_action_name

class SingleAssetTradingEnvironment(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self,
                 config: dict):
        super(SingleAssetTradingEnvironment, self).__init__()

        self.positions = {
            "LONG": 0,
            "SHORT": 1,
            "FLAT": 2
        }
        self.actions = {
            "BUY": 0,
            "SELL": 1,
            "HOLD": 2
        }

        self.df = pd.read_csv(config["data_path"])[["open","high","close","low", "volume"]]
        self.initial_account_balance = config["initial_account_balance"]
        self.current_account_balance = config["initial_account_balance"]
        self.unavailable_action_penalization_reward = config["unavailable_action_penalization_reward"]
        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.current_step = 0
        self.total_rewards = 0
        self.timestamp_reward = 0
        self.total_returns = 0
        self.trade_commission = 0.001
        self.normalization_factor = 999999

        self.trading_history = self._initialize_trading_history()
        self.observation_agent_states = self._initialize_observation_agent_states()
        self.action_space = gym.spaces.Discrete(len(list(self.actions.keys())))
        self.observation_space = self._define_observation_space()

        self.action_method = SingleAssetDiscreteFullAction(self.trade_commission)
        self.reward_generator = RewardGenerator(config["reward_method"], config["reward_window"])
        self.renderer = SingleAssetRenderer()

    def reset(self) -> Tuple[np.array, dict]:
        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.current_account_balance = self.initial_account_balance
        self.total_returns = 0
        self.current_step = 0
        self.total_rewards = 0
        self.timestamp_reward = 0
        self.trading_history = self._initialize_trading_history()
        
        return self._next_observation()
    
    def _define_observation_space(self) -> gym.spaces.Box:
        low_agent_state = np.array([0, 0, -np.inf]) #position, action and account balance low observations
        low_market_state = np.array([-np.inf for _ in range(self.df.shape[1])]) #low for all asset features for window size + current position timesteps

        high_agent_state = np.array([2, 2, np.inf]) #position, action and account balance high observations
        high_market_state = np.array([np.inf for _ in range(self.df.shape[1])]) #high for all asset features for window size + current position timesteps

        low_bound_observation_space = np.concatenate((low_market_state, low_agent_state)) #concatenate low agent state and low market state arrays
        high_bound_observation_space = np.concatenate((high_market_state, high_agent_state)) #concatenate high agent state and low market state arrays

        return gym.spaces.Box(low=low_bound_observation_space, high=high_bound_observation_space, shape=low_bound_observation_space.shape)

    def _initialize_observation_agent_states(self) -> np.array:
        agent_states = np.array([self.current_position, self.current_action, self.current_account_balance / self.normalization_factor])
        return agent_states

    def _update_observation_agent_states(self) -> None:
        self.observation_agent_states = np.array([self.current_position, self.current_action, self.current_account_balance / self.normalization_factor])

    def _get_observation_market_states(self) -> np.array:
        market_states = np.array([
            self.df.loc[self.current_step, "open"],
            self.df.loc[self.current_step, "high"],
            self.df.loc[self.current_step, "low"],
            self.df.loc[self.current_step, "close"],
            self.df.loc[self.current_step, "volume"]
        ])

        return market_states / self.normalization_factor
    
    def _calculate_reward(self) -> float:
        if len(self.trading_history["ACCOUNT_BALANCE"]) > 1:
            if self.current_position == 0 and self.current_action == 0:
                return self.unavailable_action_penalization_reward
            elif self.current_position == 1 and self.current_action == 1:
                return self.unavailable_action_penalization_reward
            else:
                return self.reward_generator.calculate_reward(self.trading_history["ACCOUNT_BALANCE"])
        else:
            return 0.0
        
    def _initialize_trading_history(self) -> dict:
        return {
            "ACCOUNT_BALANCE": [self.current_account_balance],
            "POSITION": [self.current_position],
            "ACTION": [self.current_action],
            "PRICE": [self.df["close"].iloc[0]],
            "TOTAL_REWARDS": [self.total_rewards],
            "STEP": [self.current_step]
        }

    def _save_trading_history(self, current_account_balance: List[float], current_position: int, current_action: int, current_price: float) -> None:
        self.trading_history["ACCOUNT_BALANCE"].append(current_account_balance)
        self.trading_history["POSITION"].append(current_position)
        self.trading_history["ACTION"].append(current_action)
        self.trading_history["PRICE"].append(current_price)
        self.trading_history["TOTAL_REWARDS"].append(self.total_rewards)
        self.trading_history["STEP"].append(self.current_step)
    
    def step(self, action: int) -> Tuple[pd.DataFrame, float, bool, dict]:
        self.current_account_balance, self.current_action, self.current_position, self.current_price, self.total_returns = self.action_method.take_action(self.df, self.trading_history, self.current_step, action)
        self.timestamp_reward = self._calculate_reward()
        self.total_rewards += self.timestamp_reward
        self._save_trading_history(self.current_account_balance, self.current_position, self.current_action, self.current_price)
        observation = self._next_observation()
        self.current_step += 1

        if self.current_account_balance <= 0 or self.current_step == self.df.shape[0] - 1:
            done = True
        else:
            done = False

        info = {
            "ACCOUNT BALANCE": self.current_account_balance,
            "TOTAL RETURNS": self.total_returns,
            "TOTAL REWARDS": self.total_rewards,
            "AGENT POSITION": get_position_name(self.current_position),
            "AGENT ACTION": get_action_name(self.current_action),
            "STEP": self.current_step
        }
        print(info)

        return observation, self.timestamp_reward, done, info

    def render(self, mode="console") -> None:
        self.renderer.render(mode, self.trading_history)

    def _next_observation(self) -> np.array:
        market_states_observation = self._get_observation_market_states()
        self._update_observation_agent_states()
        observation = np.concatenate((market_states_observation, self.observation_agent_states))

        return observation