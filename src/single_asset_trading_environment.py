import random
import gymnasium as gym
import pandas as pd
import numpy as np

from typing import Tuple
from gymnasium.spaces import Discrete, Box


class SingleAssetTradingEnvironment(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, config: dict):
        super(SingleAssetTradingEnvironment, self).__init__()

        self.df = config["df"]
        self.initial_account_balance = config["initial_account_balance"]
        self.window_size = config["window_size"]
        self.account_balance = config["initial_account_balance"]
        self.trade_commission = 0.001
        self.normalization_factor = 999999999
        self.accumulated_returns = 0
        self.entry_price = None

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
        self.timestamp_reward = 0
        self.observation_agent_states = self._initialize_observation_agent_states()

        self.action_space = Discrete(len(list(self.actions.keys())))
        self.observation_space = self._define_observation_space()

    def reset(self) -> np.array:
        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.account_balance = self.initial_account_balance
        self.accumulated_returns = 0
        self.current_step = self.window_size
        self.entry_price = None
        self.timestamp_reward = 0

        return self._next_observation()
    
    def _define_observation_space(self) -> gym.spaces.Box:
        low_agent_state = np.array([[0, 0, -np.inf] for _ in range(self.window_size)]) #position, action and account balance low observations
        low_market_state = np.array([[-np.inf for _ in range(self.df.shape[1])] for _ in range(self.window_size)]) #low for all asset features for window size timesteps

        high_agent_state = np.array([[2, 2, np.inf] for _ in range(self.window_size)]) #position, action and account balance high observations
        high_market_state = np.array([[np.inf for _ in range(self.df.shape[1])] for _ in range(self.window_size)]) #high for all asset features for window size timesteps

        low_bound_observation_space = np.concatenate((low_market_state, low_agent_state), axis=1) #concatenate low agent state and low market state arrays
        high_bound_observation_space = np.concatenate((high_market_state, high_agent_state), axis=1) #concatenate high agent state and low market state arrays

        return Box(low=low_bound_observation_space, high=high_bound_observation_space, shape=(self.window_size, low_bound_observation_space.shape[1]))

    def _initialize_observation_agent_states(self) -> np.array:
        account_balances = [self.account_balance / self.normalization_factor] * self.window_size
        current_actions = [self.current_action] * self.window_size
        current_positions = [self.current_position] * self.window_size

        return np.array([account_balances, current_actions, current_positions]).T

    def _update_observation_agent_states(self):
        current_agent_state = np.array([[self.current_position], [self.current_action], [self.account_balance / self.normalization_factor]]).T
        self.observation_agent_states = np.concatenate((self.observation_agent_states[1:,:], current_agent_state), axis=0)

    def _get_observation_market_states(self) -> np.array:
        market_states = np.array([
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'open'].values / self.normalization_factor,
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'high'].values / self.normalization_factor,
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'min'].values / self.normalization_factor,
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'close'].values / self.normalization_factor
        ])

        return market_states.T

    def _calculate_trade_profit(self, current_price: float) -> float:
        if self.current_position == 0:
            trade_profit = ((current_price - self.entry_price) / self.entry_price) * (1 - self.trade_commission)
        elif self.current_position == 1:
            trade_profit = ((self.entry_price - current_price) / self.entry_price) * (1 - self.trade_commission)
        else:
            trade_profit = 0
        
        return trade_profit
    
    def _take_action(self, action: int) -> None:
        current_price = random.uniform(self.df.loc[self.current_step, "open"], self.df.loc[self.current_step, "close"]) #ESTO ES UNA EXAGERACIÓN PARA SIMULAR QUE EN LA PRACTICA NO ENTRAS JUSTO EN EL PRECIO DE OPEN NUNCA
        self.timestamp_reward = 0

        if self.current_position == 0: #esto significa que la posicion es LONG por lo que puedo holdear (HOLD) o vender (SELL)
            if action == 0: #esto significa que decido comprar (BUY) y es una accion que no se puede hacer porque ya he comprado con el 100% de mi patrimonio
                self.timestamp_reward = -1
            
            elif action == 1: #esto significa que decido vender (SELL) por lo que paso a la posicion FLAT
                self.current_action = self.actions["SELL"]
                trade_profit = self._calculate_trade_profit(current_price) #CALCULO EL PROFIT DE MI TRADE DESCONTANDO LA COMISION
                self.accumulated_returns += trade_profit
                self.account_balance *= (1 + trade_profit)
                self.current_position  = self.positions["FLAT"]

                self.timestamp_reward = trade_profit
            
            elif action == 2: #esto significa que decido holdear (HOLD) por lo que me mantengo en la posicion LONG
                pass
        
        elif self.current_position == 1: #esto significa que la posicion es SHORT por lo que puedo holdear (HOLD) o vender (SELL)
            if action == 0: #esto significa que decido comprar (BUY) pero es una accion que no puedo porque ya tengo el 100% de mi patrimonio invertido en posicion SHORT
                self.timestamp_reward = -1
            
            elif action == 1: #esto significa que decido vender (SELL) por lo que paso a la posicion FLAT
                self.current_action = self.actions["SELL"]
                trade_profit = self._calculate_trade_profit(current_price) #CALCULO EL PROFIT DE MI TRADE DESCONTANDO LA COMISION
                self.accumulated_returns += trade_profit
                self.account_balance *= (1 + trade_profit)
                self.current_position  = self.positions["FLAT"]

                self.timestamp_reward = trade_profit
            
            elif action == 2: # esto significa que decido holdear (HOLD) por lo que la posicion sigue siendo SHORT
                self.current_action = self.actions["HOLD"]

        elif self.current_position == 2: #esto significa que la posicion es FLAT por lo que puedo comprar (BUY), vender (SELL) o no hacer nada (HOLD)
            if action == 0: #esto significa que decido comprar (BUY) por lo que entro en la posicion LONG
                self.current_action = self.actions["BUY"]
                updated_account_balance = (self.account_balance * (1 - self.trade_commission)) #APLICO LA COMISION A MI PATRIMONIO POR HABER COMPRADO
                self.accumulated_returns -= self.trade_commission
                self.account_balance = updated_account_balance
                self.entry_price = current_price
                self.current_position = self.positions["LONG"]

            elif action == 1: #esto significa que decido vender (SELL) por lo que entro en la posicion SHORT
                self.current_action = self.actions["SELL"]
                updated_account_balance = (self.account_balance * (1 - self.trade_commission)) #APLICO LA COMISION A MI PATRIMONIO POR HABER COMPRADO
                self.accumulated_returns -= self.trade_commission
                self.account_balance = updated_account_balance
                self.entry_price = current_price
                self.current_position = self.positions["SHORT"]

            elif action == 2: #esto siginifica que decido no hacer nada (HOLD) por lo que sigo en la posicion FLAT observando el mercado
                self.current_action = self.actions["HOLD"]

    def step(self, action: int) -> Tuple[pd.DataFrame, float, bool, dict]:
        self._take_action(action)

        self.current_step += 1

        if self.account_balance <= 0:
            done = True
        else:
            done = False

        observation = self._next_observation()

        if observation is None:
            done = True
        
        info = {}

        return observation, self.timestamp_reward, done, info

    def render(self, mode="human"):
        if mode == "human":
            print("----------------------------------------------------")
            print(f"ACCOUNT BALANCE: {self.account_balance}")
            print(f"ACCUMULATED RETURNS: {self.accumulated_returns}")
            print("----------------------------------------------------")
            print()
            print()
        else:
            pass

    def _next_observation(self):
        market_states_observation = self._get_observation_market_states()
        if market_states_observation.shape[0] == self.window_size:

            if self.current_step != self.window_size:
                self._update_observation_agent_states()

            observation = np.append(market_states_observation, self.observation_agent_states, axis=1)

        else:
            observation = None

        return observation