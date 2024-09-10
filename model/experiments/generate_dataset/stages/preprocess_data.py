import gzip
import json
import os
import pandas as pd
import sys
from tqdm import tqdm

from bayesbet.nhl.data_utils import extract_game_data


def main(season):
    with gzip.open(f'../data/raw/{season}/games.json.gz', 'rb') as f:
        games_json = json.loads(f.read().decode('utf-8'))

    games_data_frames = []
    for game_json in tqdm(games_json):
        game_data_frame, _ = extract_game_data(game_json)
        games_data_frames.append(game_data_frame)

    # Drop pre-season, all-star, and other game types
    games = pd.concat(games_data_frames, ignore_index=True)
    games = games[~games["game_type"].isin(["Pr", "A", "Other"])]
    games = games.reset_index(drop=True)
    
    os.makedirs(f"../data/preprocessed/{season}", exist_ok=True)
    games.to_parquet(f"../data/preprocessed/{season}/games.parquet")
    

if __name__ == "__main__":
    season = sys.argv[1]
    main(season)
