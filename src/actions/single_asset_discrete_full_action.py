import pandas as pd

from typing import Tuple

from actions.action import Action

class SingleAssetDiscreteFullAction(Action):
    def __init__(self, trade_commission: float):
        super().__init__(trade_commission)

    def take_action(self, df: pd.DataFrame,
                    trading_history: dict,
                    current_step: int,
                    action: int) -> Tuple[float, int, int, float, float]:
        #current_price = random.uniform(self.df.loc[self.current_step, "open"], self.df.loc[self.current_step, "close"]) #ESTO ES UNA EXAGERACIÓN PARA SIMULAR QUE EN LA PRACTICA NO ENTRAS JUSTO EN EL PRECIO DE OPEN NUNCA
        #current_price = self.df.loc[self.current_step, "close"] #COGEMOS EL VALOR DEL CLOSE DIRECTAMENTE AUNQUE EN LA REALIDAD ES DIFICIL O IMPOSIBLE PILLAR JUSTO ESE VALOR
        current_price = (df.loc[current_step, "open"] + df.loc[current_step, "close"]) / 2 #COGEMOS EL VALOR MEDIO ENTRE EL OPEN Y CLOSE PARA SIMULAR
        account_balance = trading_history["ACCOUNT_BALANCE"][-1]
        current_position = trading_history["POSITION"][-1]

        if len(trading_history["ACCOUNT_BALANCE"]) > 1:
            if current_position == 0: #LONG
                price_pct_change = (current_price - trading_history["PRICE"][-1]) / trading_history["PRICE"][-1]

                if action == 0: #BUY
                    pass
                elif action == 1: #SELL
                    account_balance *= (1 + price_pct_change) * (1 - self.trade_commission)
                    current_position = 2 #FLAT
                elif action == 2: #HOLD
                    account_balance *= (1 + price_pct_change)

            elif current_position == 1: #SHORT
                price_pct_change = (trading_history["PRICE"][-1] - current_price) / trading_history["PRICE"][-1]

                if action == 0: #BUY
                    account_balance *= (1 - price_pct_change) * (1 - self.trade_commission)
                    current_position = 2 #FLAT
                elif action == 1: #SELL
                    pass
                elif action == 2: #HOLD
                    account_balance *= (1 + price_pct_change)

            elif current_position == 2: #FLAT
                if action == 0: #BUY
                    account_balance *= (1 - self.trade_commission)
                    current_position = 0 #LONG
                elif action == 1: #SELL
                    account_balance *= (1 - self.trade_commission)
                    current_position = 1 #SHORT
                elif action == 2: #HOLD
                    pass
        
        total_returns = (account_balance / trading_history["ACCOUNT_BALANCE"][0]) - 1.0
        
        return account_balance, action, current_position, current_price, total_returns