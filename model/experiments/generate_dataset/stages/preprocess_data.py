import gzip
import json
import os
import pandas as pd
import sys
from tqdm import tqdm

from bayesbet.nhl.data_utils import extract_game_data, extract_shot_data


def main(season):
    with gzip.open(f'../data/raw/{season}/games.json.gz', 'rb') as f:
        games_json = json.loads(f.read().decode('utf-8'))

    with gzip.open(f'../data/raw/{season}/play_by_play.json.gz', 'rb') as f:
        play_by_play_json = json.loads(f.read().decode('utf-8'))

    games_data_frames = []
    for game_json in tqdm(games_json):
        game_data_frame, _ = extract_game_data(game_json)
        games_data_frames.append(game_data_frame)

    # Drop pre-season, all-star, and other game types
    games = pd.concat(games_data_frames, ignore_index=True)
    games = games[~games["game_type"].isin(["Pr", "A", "Other"])]
    games = games.reset_index(drop=True)

    shots_data_frames = []
    for game_id in games["game_pk"]:
        game_play_by_play_json = play_by_play_json[str(game_id)]
        shot_data_frame = extract_shot_data(game_play_by_play_json)
        shots_data_frames.append(shot_data_frame)

    shots = pd.concat(shots_data_frames, ignore_index=True)
    
    os.makedirs(f"../data/preprocessed/{season}", exist_ok=True)
    games.to_parquet(f"../data/preprocessed/{season}/games.parquet")
    shots.to_parquet(f"../data/preprocessed/{season}/shots.parquet")
    

if __name__ == "__main__":
    season = sys.argv[1]
    main(season)
