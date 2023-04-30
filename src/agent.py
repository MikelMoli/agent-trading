import ray
import os

from ray import tune
from ray.tune.registry import register_env
from ray.tune.logger import TBXLoggerCallback

from single_asset_trading_environment import SingleAssetTradingEnvironment

def create_env(env_config):
        return SingleAssetTradingEnvironment(env_config)

if __name__ == "__main__":
    data_path = os.path.abspath("../data/merged/cleaned_1_H_merged_data.csv")
    initial_account_balance = 10000
    window_size = 5

    ray.init()
    register_env("single-asset-trading-environment", create_env)
    tune.run("PPO",
             config = {
                 "env": "single-asset-trading-environment",
                 "framework": "torch",
                 "num_workers": 1,
                 "num_envs_per_worker": 1,
                 "train_batch_size": 128, #esto indica cuantos episodios tiene un batch
                 "batch_mode": "truncate_episodes", #esto asegura que los batches siempre tengan la misma cantidad de episodios
                 "evaluation_interval": 10, #esto indica que el agente se evaluará cada 10 intervalos (cada intervalo es un batch con 128 episodios)
                 "evaluation_num_episodes": 128 * 4, #esto indica que el agente se evaluará en 128 * 4 episodios (lo que es equivalente a 4 batches)
                 "num_gpus": 0,
                 "model": { # este modelo tiene esta estructura -> LSTM(64) -> FC(128) + RELU -> FC(64) + RELU -> FC(32) + RELU
                    "fcnet_hiddens": [128, 64, 32],
                    "fcnet_activation": "relu",
                    "use_lstm": True,
                    "lstm_cell_size": 64,
                    },
                 "env_config": {
                    "data_path": data_path,
                    "initial_account_balance": initial_account_balance,
                    "window_size": window_size
                }
             },
            checkpoint_at_end=True,
            callbacks=[TBXLoggerCallback()],
            local_dir=os.path.abspath("../agents_results/")
    )