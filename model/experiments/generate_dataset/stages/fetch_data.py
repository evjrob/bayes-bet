from datetime import date
import gzip
import json
import os
import sys
from tqdm import tqdm

from bayesbet.nhl.stats_api import (
    request_games_json,
    request_play_by_play_json,
    request_shifts_json,
)


def main(season, start_date, end_date):
    total_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days

    games = []
    play_by_play = {}
    shifts = {}    

    game_json = request_games_json(start_date)
    previous_game_date = start_date
    next_game_date = game_json["nextDate"]
    if len(game_json["games"]) > 0:
        games.append(game_json)

    with tqdm(total=total_days) as pbar:
        while next_game_date <= end_date:
            game_json = request_games_json(next_game_date)
            for game in game_json["games"]:
                game_id = game["id"]
                game_play_by_play = request_play_by_play_json(game_id)
                play_by_play[game_id] = game_play_by_play
                game_shifts = request_shifts_json(game["id"])
                shifts[game_id] = game_shifts
            days_progress = (
                date.fromisoformat(next_game_date)
                - date.fromisoformat(previous_game_date)
            ).days
            previous_game_date = next_game_date
            next_game_date = game_json["nextDate"]
            games.append(game_json)

            pbar.update(days_progress)

    
    os.makedirs(f"../data/raw/{season}", exist_ok=True)
    games_json_data = json.dumps(games, indent=2).encode('utf-8')
    with gzip.open(f'../data/raw/{season}/games.json.gz', 'wb') as f:
        f.write(games_json_data)

    play_by_play_json_data = json.dumps(play_by_play, indent=2).encode('utf-8')
    with gzip.open(f'../data/raw/{season}/play_by_play.json.gz', 'wb') as f:
        f.write(play_by_play_json_data)

    shifts_json_data = json.dumps(shifts, indent=2).encode('utf-8')
    with gzip.open(f'../data/raw/{season}/shifts.json.gz', 'wb') as f:
        f.write(shifts_json_data)

if __name__ == "__main__":
    season = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    main(season, start_date, end_date)
