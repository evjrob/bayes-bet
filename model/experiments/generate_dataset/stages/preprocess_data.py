import gzip
import json
import os
import pandas as pd
from tqdm import tqdm

from bayesbet.nhl.stats_api import extract_game_data


def main():
    with gzip.open('../data/raw/games.json.gz', 'rb') as f:
        games_json = json.loads(f.read().decode('utf-8'))

    games_data_frames = []
    for game_json in tqdm(games_json):
        game_data_frame, _ = extract_game_data(game_json)
        games_data_frames.append(game_data_frame)

    # Drop pre-season, all-star, and other game types
    games = games[~games["game_type"].isin(["Pr", "A", "Other"])]
    games = games.reset_index(drop=True)
    
    games = pd.concat(games_data_frames, ignore_index=True)
    os.makedirs("../data/preprocessed", exist_ok=True)
    games.to_parquet("../data/preprocessed/games.parquet")
    

if __name__ == "__main__":
    main()
