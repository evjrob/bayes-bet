import os
import pandas as pd


def main():
    # Split data into training and test sets based on holding out the games from
    # the most recent complete season onward.
    games = pd.read_parquet("../data/preprocessed/games.parquet")
    training_split_season = 20222023
    training_games = games[games["season"] < training_split_season]
    training_games = training_games.reset_index(drop=True)
    testing_games = games[games["season"] >= training_split_season]
    testing_games = testing_games.reset_index(drop=True)
    
    os.makedirs("../data/final/train", exist_ok=True)
    os.makedirs("../data/final/test", exist_ok=True)
    training_games.to_parquet("../data/final/train/games.parquet")
    testing_games.to_parquet("../data/final/test/games.parquet")
    

if __name__ == "__main__":
    main()