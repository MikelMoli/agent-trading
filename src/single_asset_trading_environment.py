import gymnasium as gym
import pandas as pd
import numpy as np

from typing import Tuple, List, Optional
from gymnasium.spaces import Discrete, Box
from rewards.reward_generator_facade import RewardGeneratorFacade
from actions.single_asset_discrete_full_action import SingleAssetDiscreteFullAction
from renders.single_asset_renderer import SingleAssetRenderer

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

        self.df = pd.read_csv(config["data_path"])[["open","high","close","low"]]
        self.initial_account_balance = config["initial_account_balance"]
        self.window_size = config["window_size"]
        self.current_step = config["window_size"]
        self.current_account_balance = config["initial_account_balance"]
        self.unavailable_action_penalization_reward = config["unavailable_action_penalization_reward"]
        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.total_rewards = 0
        self.timestamp_reward = 0
        self.total_returns = 0
        self.trade_commission = 0.001
        self.normalization_factor = 999999

        self.trading_history = self._initialize_trading_history()
        self.observation_agent_states = self._initialize_observation_agent_states()
        self.action_space = Discrete(len(list(self.actions.keys())))
        self.observation_space = self._define_observation_space()

        self.action_method = SingleAssetDiscreteFullAction(self.trade_commission)
        self.reward_generator = RewardGeneratorFacade(config["reward_method"], config["reward_window"])
        self.renderer = SingleAssetRenderer()

    def reset(self, seed: Optional[int] = 42) -> Tuple[np.array, dict]:
        super().reset(seed=seed)

        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.current_account_balance = self.initial_account_balance
        self.total_returns = 0
        self.current_step = self.window_size
        self.total_rewards = 0
        self.timestamp_reward = 0
        self.trading_history = self._initialize_trading_history()

        info = {
            "ACCOUNT BALANCE": self.current_account_balance,
            "TOTAL RETURNS": self.total_returns,
            "TOTAL REWARDS": self.total_rewards,
            "AGENT POSITION": self.current_position,
            "AGENT ACTION": self.current_action,
            "STEP": self.current_step
        }
        
        return self._next_observation(), info
    
    def _define_observation_space(self) -> gym.spaces.Box:
        low_agent_state = np.array([[0, 0, -np.inf] for _ in range(self.window_size + 1)]) #position, action and account balance low observations
        low_market_state = np.array([[-np.inf for _ in range(self.df.shape[1])] for _ in range(self.window_size + 1)]) #low for all asset features for window size + current position timesteps

        high_agent_state = np.array([[2, 2, np.inf] for _ in range(self.window_size + 1)]) #position, action and account balance high observations
        high_market_state = np.array([[np.inf for _ in range(self.df.shape[1])] for _ in range(self.window_size + 1)]) #high for all asset features for window size + current position timesteps

        low_bound_observation_space = np.concatenate((low_market_state, low_agent_state), axis=1) #concatenate low agent state and low market state arrays
        high_bound_observation_space = np.concatenate((high_market_state, high_agent_state), axis=1) #concatenate high agent state and low market state arrays

        return Box(low=low_bound_observation_space, high=high_bound_observation_space, shape=(self.window_size + 1, low_bound_observation_space.shape[1]))

    def _initialize_observation_agent_states(self) -> np.array:
        agent_states = [[self.current_position, self.current_action, self.current_account_balance / self.normalization_factor]] * (self.window_size + 1)
        return np.array(agent_states)

    def _update_observation_agent_states(self) -> None:
        current_agent_state = np.array([[self.current_position, self.current_action, self.current_account_balance / self.normalization_factor]])
        self.observation_agent_states = np.concatenate((self.observation_agent_states[1:,:], current_agent_state), axis=0)

    def _get_observation_market_states(self) -> np.array:
        market_states = np.array([
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'open'].values,
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'high'].values,
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'low'].values,
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'close'].values
        ])

        return market_states.T / self.normalization_factor
    
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
        
    def step(self, action: int) -> Tuple[pd.DataFrame, float, bool, bool, dict]:
        current_state = self.action_method.take_action(self.df, self.trading_history, self.current_step, action)
        self.current_account_balance = current_state["account_balance"]
        self.total_returns = (self.current_account_balance / self.initial_account_balance) - 1
        self.current_position = current_state["position"]
        self.current_action = current_state["action"]
        self.current_price = current_state["price"]
        self.timestamp_reward = self._calculate_reward()
        self.total_rewards += self.timestamp_reward

        self._save_trading_history(self.current_account_balance, self.current_position, self.current_action, self.current_price)
        observation = self._next_observation()

        self.current_step += 1
        if self.current_account_balance <= 0 or self.current_step == self.df.shape[0] - 1:
            terminated = True
        else:
            terminated = False

        info = {
            "ACCOUNT BALANCE": self.current_account_balance,
            "TOTAL RETURNS": self.total_returns,
            "TOTAL REWARDS": self.total_rewards,
            "AGENT POSITION": self._get_position_name(self.current_position),
            "AGENT ACTION": self._get_action_name(self.current_action),
            "STEP": self.current_step
        }
        #if self.current_step % 5000 == 0:
        print(info)

        return observation, self.timestamp_reward, terminated, False, info
    
    def _get_action_name(self, action: int) -> str:
        if action == 0:
            return "BUY"
        elif action == 1:
            return "SELL"
        elif action == 2:
            return "HOLD"
    
    def _get_position_name(self, position: int) -> str:
        if position == 0:
            return "LONG"
        elif position == 1:
            return "SHORT"
        elif position == 2:
            return "FLAT"

    def render(self, mode="console") -> None:
        self.renderer.render(mode, self.trading_history)

    def _next_observation(self) -> np.array:
        market_states_observation = self._get_observation_market_states()
        self._update_observation_agent_states()
        observation = np.append(market_states_observation, self.observation_agent_states, axis=1)

        return observation