import os
import pandas as pd
import yaml


def main(train_seasons, test_seasons):
    # Split data into training and test sets based on holding out the games from
    # the most recent complete season onward.
    games = pd.read_parquet("../data/preprocessed/games.parquet")
    training_games = games[games["season"].isin(train_seasons)]
    training_games = training_games.reset_index(drop=True)
    testing_games = games[games["season"].isin(test_seasons)]
    testing_games = testing_games.reset_index(drop=True)
    
    os.makedirs("../data/final/train", exist_ok=True)
    os.makedirs("../data/final/test", exist_ok=True)
    training_games.to_parquet("../data/final/train/games.parquet")
    testing_games.to_parquet("../data/final/test/games.parquet")
    

if __name__ == "__main__":
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)
    train_seasons = params["splits"]["train"]
    test_seasons = params["splits"]["test"]

    main()