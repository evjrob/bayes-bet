from datetime import date
import gzip
import json
import os
from tqdm import tqdm
import yaml

from bayesbet.nhl.stats_api import request_games_json


def main():
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)

    start_date = params["fetch_data"]["start_date"]
    end_date = params["fetch_data"]["end_date"]
    total_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days

    games = []

    game_json = request_games_json(start_date)
    previous_game_date = start_date
    next_game_date = game_json["nextDate"]
    if len(game_json["games"]) > 0:
        games.append(game_json)

    with tqdm(total=total_days) as pbar:
        while next_game_date <= end_date:
            game_json = request_games_json(next_game_date)
            days_progress = (
                date.fromisoformat(next_game_date)
                - date.fromisoformat(previous_game_date)
            ).days
            previous_game_date = next_game_date
            next_game_date = game_json["nextDate"]
            games.append(game_json)

            pbar.update(days_progress)

    
    json_data = json.dumps(games, indent=2).encode('utf-8')
    os.makedirs("../data/raw", exist_ok=True)
    with gzip.open('../data/raw/games.json.gz', 'wb') as f:
        f.write(json_data)

if __name__ == "__main__":
    main()
