import os

import pandas as pd

from environments.single_asset_trading_environment import SingleAssetTradingEnvironment

def create_datetime(row) -> pd.Series:
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
    df = df[(df["date"].dt.hour % 12 == 0) & (df["date"].dt.minute == 0)]    
    df = df[["open", "high", "close", "low"]].reset_index()

    print("DATAFRAME HAS BEEN CLEANED.")

    return df

if __name__ == "__main__":
    #df = pd.read_csv("../data/merged/merged_data.csv")
    #df = clean_df(df)
    #df.to_csv("../data/merged/cleaned_12_H_merged_data.csv", index=False)
    df = pd.read_csv("../data/merged/cleaned_1_H_merged_data.csv")[["open", "high", "close", "low"]]

    data_path = os.path.abspath("../data/merged/cleaned_1_H_merged_data.csv")
    initial_account_balance = 10000
    window_size = 50
    reward_window = 24
    reward_method = "simple-profit"
    render_mode = "console"
    unavailable_action_penalization_reward = -1
    epochs = 1
    episodes_per_epoch = df.shape[0] - (window_size + 1)

    env_config = {
        "data_path": data_path,
        "initial_account_balance": initial_account_balance,
        "window_size": window_size,
        "reward_window": reward_window,
        "reward_method": reward_method,
        "unavailable_action_penalization_reward": unavailable_action_penalization_reward
    }

    env = SingleAssetTradingEnvironment(env_config)
    new_obs, _ = env.reset()

    total_reward = 0
    terminated = False
    for episode in range(episodes_per_epoch):
        current_action = env.action_space.sample()
        new_obs, reward, terminated, _, _ = env.step(current_action)
        total_reward += reward

        if episode % 1000 == 0 and episode != 0:
            print(f"EPISODE={episode}")
            env.render(mode="console")
        
        if terminated:
            break
    
    env.reset()