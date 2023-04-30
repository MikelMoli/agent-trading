import os

import pandas as pd

from single_asset_trading_environment import SingleAssetTradingEnvironment

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
    #df = pd.read_csv("../data/merged/merged_data.csv")
    #df = clean_df(df)
    #df.to_csv("../data/merged/cleaned_1_H_merged_data.csv", index=False)
    df = pd.read_csv("../data/merged/cleaned_1_H_merged_data.csv")[["open", "high", "close", "min"]]

    data_path = os.path.abspath("../data/merged/cleaned_1_H_merged_data.csv")
    initial_account_balance = 10000
    window_size = 50
    epochs = 1
    episodes_per_epoch = df.shape[0] - (window_size + 1)

    env_config = {
        "data_path": data_path,
        "initial_account_balance": initial_account_balance,
        "window_size": window_size
    }

    env = SingleAssetTradingEnvironment(env_config)
    new_obs, _ = env.reset()

    total_reward = 0
    terminated = False
    for epoch in range(epochs):
        print(f"EPOCH={epoch}\n")
        for episode in range(episodes_per_epoch):
            action = env.action_space.sample()
            new_obs, reward, terminated, _, _ = env.step(action)
            total_reward += reward

            if episode % 1000 == 0:
                print(f"EPISODE={episode}")
                env.render()
            
            if terminated:
                break
        
        env.reset()