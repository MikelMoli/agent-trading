import numpy as np
import matplotlib.pyplot as plt

from renders.render import Render
from utils.single_asset_trading_utils import get_position_name, get_action_name

class SingleAssetRenderer(Render):
    def __init__(self):
        super().__init__()

    def _console_render(self, trading_history: dict) -> None:
        print("----------------------------------------------------")
        print(f"ACCOUNT BALANCE: {trading_history['ACCOUNT_BALANCE'][-1]}")
        print(f"TOTAL RETURNS: {(trading_history['ACCOUNT_BALANCE'][-1] / trading_history['ACCOUNT_BALANCE'][0]) - 1.0}")
        print(f"TOTAL REWARDS: {trading_history['TOTAL_REWARDS'][-1]}")
        print(f"AGENT POSITION: {get_position_name(trading_history['POSITION'][-1])}")
        print(f"AGENT ACTION: {get_action_name(trading_history['ACTION'][-1])}")
        print(f"STEP: {trading_history['STEP'][-1]}")
        print("----------------------------------------------------")
        print()
        print()

    def _human_render(self, trading_history: dict) -> None:
        total_returns = (trading_history['ACCOUNT_BALANCE'][-1] / trading_history['ACCOUNT_BALANCE'][0]) - 1.0
        percentage_total_returns = np.round(total_returns, 4) * 100
        buy_actions = [i for i in range(len(trading_history["ACTION"])) if trading_history["ACTION"][i] == 0]
        sell_actions = [i for i in range(len(trading_history["ACTION"])) if trading_history["ACTION"][i] == 1]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20,10))

        ax1.set_title(f"ACCOUNT BALANCE HISTORY | RETURNS {percentage_total_returns}%", fontsize=14)
        ax1.plot(trading_history["ACCOUNT_BALANCE"])
        ax1.legend(["ACCOUNT BALANCE"])
        ax1.grid()
        
        ax2.set_title(f"AGENT TRADING HISTORY | RETURNS {percentage_total_returns}%", fontsize=14)
        ax2.plot(trading_history["PRICE"])
        ax2.scatter(x=buy_actions, y=np.array(trading_history["PRICE"])[buy_actions], marker="^", color="green")
        ax2.scatter(x=sell_actions, y=np.array(trading_history["PRICE"])[sell_actions], marker="v", color="red")
        ax2.legend(["ASSET PRICE", "BUY", "SELL"], fontsize=12)
        ax2.grid()
        plt.show()

    def render(self, mode: str, trading_history: dict) -> None:
        if mode == "console":
            self._console_render(trading_history)
        elif mode == "human":
            self._human_render(trading_history)
        else:
            raise NotImplementedError(f"{self.mode} render mode is not supported.")
            