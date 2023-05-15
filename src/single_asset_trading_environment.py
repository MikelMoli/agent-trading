import random
import gymnasium as gym
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from typing import Tuple, Optional
from gymnasium.spaces import Discrete, Box


class SingleAssetTradingEnvironment(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, config: dict):
        super(SingleAssetTradingEnvironment, self).__init__()

        self.df = pd.read_csv(config["data_path"])[["open","high","close","min"]]
        self.initial_account_balance = config["initial_account_balance"]
        self.window_size = config["window_size"]
        self.account_balance = config["initial_account_balance"]
        self.total_returns = 0
        self.trade_commission = 0.001
        self.normalization_factor = 999999

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
        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.trading_history = {}
        self.total_rewards = 0
        self.timestamp_reward = 0

        self._initialize_trading_history()
        self.observation_agent_states = self._initialize_observation_agent_states()
        self.action_space = Discrete(len(list(self.actions.keys())))
        self.observation_space = self._define_observation_space()

    def reset(self, seed: Optional[int] = 42, options: Optional[dict] = None) -> Tuple[np.array, dict]:
        super().reset(seed=seed)

        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.account_balance = self.initial_account_balance
        self.total_returns = 0
        self.current_step = self.window_size
        self.total_rewards = 0
        self.timestamp_reward = 0
        self._initialize_trading_history()

        info = {
            "ACCOUNT BALANCE": self.account_balance,
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
        agent_states = [[self.current_position, self.current_action, self.account_balance / self.normalization_factor]] * (self.window_size + 1)
        return np.array(agent_states)

    def _update_observation_agent_states(self) -> None:
        current_agent_state = np.array([[self.current_position, self.current_action, self.account_balance / self.normalization_factor]])
        self.observation_agent_states = np.concatenate((self.observation_agent_states[1:,:], current_agent_state), axis=0)

    def _get_observation_market_states(self) -> np.array:
        market_states = np.array([
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'open'].values,
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'high'].values,
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'min'].values,
            self.df.loc[(self.current_step - self.window_size): (self.current_step), 'close'].values
        ])

        return market_states.T / self.normalization_factor
    
    def _take_action(self, action: int) -> None:
        #current_price = random.uniform(self.df.loc[self.current_step, "open"], self.df.loc[self.current_step, "close"]) #ESTO ES UNA EXAGERACIÓN PARA SIMULAR QUE EN LA PRACTICA NO ENTRAS JUSTO EN EL PRECIO DE OPEN NUNCA
        current_price = self.df.loc[self.current_step, "close"]

        if len(self.trading_history["ACCOUNT_BALANCE"]) > 1:

            if self.current_position == 0: #LONG
                price_pct_change = (current_price - self.trading_history["PRICE"][-1]) / self.trading_history["PRICE"][-1]

                if action == 0: #BUY
                    self.current_action = self.actions["BUY"]
                elif action == 1: #SELL
                    self.account_balance *= (1 + price_pct_change) * (1 - self.trade_commission)
                    self.current_action = self.actions["SELL"]
                    self.current_position = self.positions["FLAT"]
                elif action == 2: #HOLD
                    self.account_balance *= (1 + price_pct_change)
                    self.current_action = self.actions["HOLD"]

            elif self.current_position == 1: #SHORT
                price_pct_change = (self.trading_history["PRICE"][-1] - current_price) / self.trading_history["PRICE"][-1]

                if action == 0: #BUY
                    self.account_balance *= (1 - price_pct_change) * (1 - self.trade_commission)
                    self.current_action = self.actions["BUY"]
                    self.current_position = self.positions["FLAT"]
                elif action == 1: #SELL
                    self.current_action = self.actions["SELL"]
                elif action == 2: #HOLD
                    self.account_balance *= (1 + price_pct_change)
                    self.current_action = self.actions["HOLD"]

            elif self.current_position == 2: #FLAT
                price_pct_change = (current_price - self.trading_history["PRICE"][-1]) / self.trading_history["PRICE"][-1]

                if action == 0: #BUY
                    self.account_balance *= (1 - self.trade_commission)
                    self.current_action = self.actions["BUY"]
                    self.current_position = self.positions["LONG"]
                elif action == 1: #SELL
                    self.account_balance *= (1 - self.trade_commission)
                    self.current_action = self.actions["SELL"]
                    self.current_position = self.positions["SHORT"]
                elif action == 2: #HOLD
                    self.current_action = self.actions["HOLD"]

        self.total_returns = (self.account_balance / self.initial_account_balance) - 1
        self._save_trading_history(current_price)

        if len(self.trading_history["ACCOUNT_BALANCE"]) > 1:
            window = 24 #X horas + la hora actual
            if self.current_position == 0 and self.current_action == 0:
                self.timestamp_reward = -1
            elif self.current_position == 1 and self.current_action == 1:
                self.timestamp_reward = -1
            else:
                self.timestamp_reward = self.account_balance / self.trading_history["ACCOUNT_BALANCE"][-min(len(self.trading_history["ACCOUNT_BALANCE"]), window)] - 1.0
        else:
            self.timestamp_reward = 0.0
        
    def _initialize_trading_history(self) -> None:
        self.trading_history = {
            "ACCOUNT_BALANCE": [self.account_balance],
            "POSITION": [self.current_position],
            "ACTION": [self.current_action],
            "PRICE": [self.df["close"].iloc[0]]
        }

    def _save_trading_history(self, current_price) -> None:
        self.trading_history["ACCOUNT_BALANCE"].append(self.account_balance)
        self.trading_history["POSITION"].append(self.current_position)
        self.trading_history["ACTION"].append(self.current_action)
        self.trading_history["PRICE"].append(current_price)
        
    def step(self, action: int) -> Tuple[pd.DataFrame, float, bool, bool, dict]:
        self._take_action(action)
        self.total_rewards += self.timestamp_reward
        observation = self._next_observation()

        self.current_step += 1

        if self.account_balance <= 0 or self.current_step == self.df.shape[0] - 1:
            terminated = True
        else:
            terminated = False

        info = {
            "ACCOUNT BALANCE": self.account_balance,
            "TOTAL RETURNS": self.total_returns,
            "TOTAL REWARDS": self.total_rewards,
            "AGENT POSITION": self._get_position_name(),
            "AGENT ACTION": self._get_action_name(),
            "STEP": self.current_step
        }
        #if self.current_step % 5000 == 0:
        print(info)

        return observation, self.timestamp_reward, terminated, False, info
    
    def _get_action_name(self) -> str:
        if self.current_action == 0:
            return "BUY"
        elif self.current_action == 1:
            return "SELL"
        elif self.current_action == 2:
            return "HOLD"
    
    def _get_position_name(self) -> str:
        if self.current_position == 0:
            return "LONG"
        elif self.current_position == 1:
            return "SHORT"
        elif self.current_position == 2:
            return "FLAT"

    def render(self, mode="console") -> None:
        if mode == "console":
            print("----------------------------------------------------")
            print(f"ACCOUNT BALANCE: {self.account_balance}")
            print(f"TOTAL RETURNS: {self.total_returns}")
            print(f"TOTAL REWARDS: {self.total_rewards}")
            print(f"AGENT POSITION: {self._get_position_name()}")
            print(f"AGENT ACTION: {self._get_action_name()}")
            print(f"STEP: {self.current_step}")
            print("----------------------------------------------------")
            print()
            print()
        elif mode == "human":
            percentage_total_returns = np.round(self.total_returns, 4) * 100
            buy_actions = [i for i in range(len(self.trading_history["ACTION"])) if self.trading_history["ACTION"][i] == 0]
            sell_actions = [i for i in range(len(self.trading_history["ACTION"])) if self.trading_history["ACTION"][i] == 1]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20,10))

            ax1.set_title(f"ACCOUNT BALANCE HISTORY | RETURNS {percentage_total_returns}%", fontsize=14)
            ax1.plot(self.trading_history["ACCOUNT_BALANCE"])
            ax1.legend(["ACCOUNT BALANCE"])
            ax1.grid()
            
            ax2.set_title(f"AGENT TRADING HISTORY | RETURNS {percentage_total_returns}%", fontsize=14)
            ax2.plot(self.trading_history["PRICE"])
            ax2.scatter(x=buy_actions, y=np.array(self.trading_history["PRICE"])[buy_actions], marker="^", color="green")
            ax2.scatter(x=sell_actions, y=np.array(self.trading_history["PRICE"])[sell_actions], marker="v", color="red")
            ax2.legend(["ASSET PRICE", "BUY", "SELL"], fontsize=12)
            ax2.grid()
            plt.show()
            

    def _next_observation(self) -> np.array:
        market_states_observation = self._get_observation_market_states()
        self._update_observation_agent_states()
        observation = np.append(market_states_observation, self.observation_agent_states, axis=1)

        return observation