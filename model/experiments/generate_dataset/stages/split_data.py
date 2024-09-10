import os
import pandas as pd
import yaml


def main(train_seasons, test_seasons):
    # Split data into training and test sets
    train_games = pd.concat(
        [pd.read_parquet(f"../data/preprocessed/{season}/games.parquet") for season in train_seasons],
        ignore_index=True
    )
    test_games = pd.concat(
        [pd.read_parquet(f"../data/preprocessed/{season}/games.parquet") for season in test_seasons],
        ignore_index=True
    )
    
    os.makedirs("../data/final/train", exist_ok=True)
    os.makedirs("../data/final/test", exist_ok=True)
    train_games.to_parquet("../data/final/train/games.parquet")
    test_games.to_parquet("../data/final/test/games.parquet")
    

if __name__ == "__main__":
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)
    train_seasons = params["splits"]["train"]
    test_seasons = params["splits"]["test"]

    main(train_seasons, test_seasons)