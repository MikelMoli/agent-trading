import ray

import pandas as pd
from ray import tune
from single_asset_trading_environment import SingleAssetTradingEnvironment

def env_creator(env_name):
    if env_name == 'single-asset-trading-environment':
        from single_asset_trading_environment import SingleAssetTradingEnvironment as env
    else:
        raise NotImplementedError
    return env

if __name__ == "__main__":
    df = pd.read_csv("../data/merged/cleaned_1_H_merged_data.csv")[["open","high","close","min"]]
    initial_account_balance = 10000
    window_size = 5

    config = {
        "df": df,
        "initial_account_balance": initial_account_balance,
        "window_size": window_size
    }

    ray.init()
    env = env_creator('single-asset-trading-environment')
    tune.register_env('single-asset-trading-environment', lambda config: env(config))
    tune.run("PPO",
             config={
                 "env": "single-asset-trading-environment",
                 "framework": "torch",
                 "num_workers": 2,
                 "num_envs_per_worker": 1,
                 "train_batch_size": 400,
                 "evaluation_interval": 1,
                 "evaluation_num_episodes": 100,
                 "num_gpus": 0
    })
    #algo = ppo.PPO(env=SingleAssetTradingEnvironment, config={
    #    "env_config": config
    #})

    #while True:
    #    print(algo.train())