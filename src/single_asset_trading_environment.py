import random
import gym
import pandas as pd
import numpy as np

from typing import Tuple
from gym import spaces

class SingleAssetTradingEnvironment(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self,
                 df: pd.DataFrame,
                 initial_account_balance: float,
                 window_size: int,
                 trade_commission: float = 0.001,
                 max_share_price_ref_for_normalization: int = 999999999,
                 max_shares_ref_for_normalization: int = 999999999,
                 max_account_balance_for_normalization: int = 999999999,
                 max_net_worth_for_normalization: int = 999999999,
                 max_shares_held_for_normalization: int = 999999999
                 ):
        
        super(SingleAssetTradingEnvironment, self).__init__()
        
        self.df = df
        self.initial_account_balance = initial_account_balance
        self.window_size = window_size
        self.trade_commission = trade_commission
        self.current_step = window_size
        self.net_worth = initial_account_balance
        self.accumulated_returns = 0
        self.entry_price = None

        #normalization variables
        self.max_share_price_ref_for_normalization = max_share_price_ref_for_normalization
        self.max_shares_ref_for_normalization = max_shares_ref_for_normalization
        self.max_account_balance_for_normalization = max_account_balance_for_normalization
        self.max_net_worth_for_normalization = max_net_worth_for_normalization
        self.max_shares_held_for_normalization = max_shares_held_for_normalization

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
        self.action_space = spaces.Discrete(len(list(self.actions.keys())))
        self.timestamp_reward = 0

    def reset(self) -> np.array:
        self.current_position = self.positions["FLAT"]
        self.current_action = self.actions["HOLD"]
        self.net_worth = self.initial_account_balance
        self.accumulated_returns = 0
        self.current_step = self.window_size

        return self._next_observation()
    
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

        if self.current_position == 2: #esto significa que la posicion es FLAT por lo que puedo comprar (BUY), vender (SELL) o no hacer nada (HOLD)
            if action == 0: #esto significa que decido comprar (BUY) por lo que entro en la posicion LONG
                self.current_action = self.actions["BUY"]
                updated_net_worth = (self.net_worth * (1 - self.trade_commission)) #APLICO LA COMISION A MI PATRIMONIO POR HABER COMPRADO
                self.accumulated_returns -= self.trade_commission
                self.net_worth = updated_net_worth
                self.entry_price = current_price
                self.current_position = self.positions["LONG"]

            elif action == 1: #esto significa que decido vender (SELL) por lo que entro en la posicion SHORT
                self.current_action = self.actions["SELL"]
                trade_profit = self._calculate_trade_profit(current_price) #CALCULO EL PROFIT DE MI TRADE DESCONTANDO LA COMISION
                self.accumulated_returns += trade_profit
                self.net_worth *= (1 + trade_profit)
                self.current_position = self.positions["SHORT"]

                self.timestamp_reward = trade_profit

            elif action == 2: #esto siginifica que decido no hacer nada (HOLD) por lo que sigo en la posicion FLAT observando el mercado
                self.current_action = self.actions["HOLD"]

        elif self.current_position == 0: #esto significa que la posicion es LONG por lo que puedo hacer holdear (HOLD) o vender (SELL)
            if action == 1: #esto significa que decido vender (SELL) por lo que paso a la posicion FLAT
                self.current_action = self.actions["SELL"]
                trade_profit = self._calculate_trade_profit(current_price) #CALCULO EL PROFIT DE MI TRADE DESCONTANDO LA COMISION
                self.accumulated_returns += trade_profit
                self.net_worth *= (1 + trade_profit)
                self.current_position  = self.positions["FLAT"]

                self.timestamp_reward = trade_profit
            
            elif action == 2: #esto signidica que decido holdear (HOLD) por lo que me mantengo en la posicion LONG
                pass

            elif action == 0: #esto significa que decido comprar (BUY) y es una accion que no se puede hacer porque ya he comprado con el 100% de mi patrimonio
                pass


    def step(self, action: int) -> Tuple[pd.DataFrame, float, bool, dict]:
        self._take_action(action)

        self.current_step += 1

        if self.net_worth <= 0:
            done = True
        else:
            done = False

        observation = self._next_observation()
        
        return observation, self.timestamp_reward, done, {}

    def render(self, mode="human"):
        if mode == "human":
            print("----------------------------------------------------")
            print(f"NET WORTH: {self.net_worth}")
            print(f"ACCUMULATED RETURNS: {self.accumulated_returns}")
            print("----------------------------------------------------")
            print()
            print()
        else:
            pass

    def _next_observation(self):
         # Get the stock data points for the last 5 days and scale to between 0-1
        frame = np.array([
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'open'].values / self.max_share_price_ref_for_normalization,
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'high'].values / self.max_share_price_ref_for_normalization,
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'min'].values / self.max_share_price_ref_for_normalization,
            self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'close'].values / self.max_share_price_ref_for_normalization,
            #self.df.loc[self.current_step: self.current_step + self.window_size - 1, 'Volume'].values / self.max_shares_ref_for_normalization,
        ])

        
        # Append additional data and scale each value to between 0-1
        #observation = np.append(frame, [[
        #    self.current_position,
        #    self.current_action,
        #    self.net_worth / self.max_net_worth_for_normalization,
        #]], axis=0)

        return frame

def create_datetime(row):
    date = row["date"]
    time = row["hour"]
    date = f"{date.split('.')[0]}-{date.split('.')[1]}-{date.split('.')[2]} {time.split(':')[0]}:{time.split(':')[1]}:00"
    row["date"] = date

    return row

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    print("CLEANING DATAFRAME...")

    df = df.apply(create_datetime, axis=1)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["date"])
    df = df[(df["date"].dt.hour % 1 == 0) & (df["date"].dt.minute == 0)]    
    df = df[["open", "high", "close", "min"]].reset_index()

    print("DATAFRAME HAS BEEN CLEANED.")

    return df

if __name__ == "__main__":
    df = pd.read_csv("../data/merged/merged_data.csv")
    df = clean_df(df)

    initial_account_balance = 10000
    window_size = 5

    env = SingleAssetTradingEnvironment(df, initial_account_balance, window_size)

    env.reset()

    total_reward = 0
    done = False

    for epoch in range(100):
        print(f"EPOCH={epoch}")
        for episode in range(df.shape[0] - (window_size + 1)):
            action = env.action_space.sample()

            new_obs, reward, done, _ = env.step(action)

            total_reward += reward

            if episode % 1000 == 0:
                print(f"EPISODE {episode}")
                env.render()
            
            if done:
                break
        
        env.reset()