import asyncio
import aiohttp
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


async def fetch_game_data(session, game_id):
    play_by_play = await request_play_by_play_json(session, game_id)
    shifts = await request_shifts_json(session, game_id)
    return game_id, play_by_play, shifts


async def main(season, start_date, end_date):
    total_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days

    games = []
    play_by_play = {}
    shifts = {}    

    async with aiohttp.ClientSession() as session:
        game_json = await request_games_json(session, start_date)
        previous_game_date = start_date
        next_game_date = game_json["nextDate"]
        if len(game_json["games"]) > 0:
            games.append(game_json)

        with tqdm(total=total_days) as pbar:
            while next_game_date <= end_date:
                game_json = await request_games_json(session, next_game_date)
                
                # Prepare concurrent requests for all games in this batch
                tasks = [fetch_game_data(session, game["id"]) for game in game_json["games"]]
                
                # Execute all requests concurrently
                results = await asyncio.gather(*tasks)
                
                # Process results
                for game_id, game_play_by_play, game_shifts in results:
                    play_by_play[game_id] = game_play_by_play
                    shifts[game_id] = game_shifts
                
                days_progress = (date.fromisoformat(next_game_date) - date.fromisoformat(previous_game_date)).days
                previous_game_date = next_game_date
                next_game_date = game_json["nextDate"]
                games.append(game_json)

                pbar.update(days_progress)

    os.makedirs(f"../data/raw/{season}", exist_ok=True)
    
    with gzip.open(f'../data/raw/{season}/games.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(games, f, indent=2)

    with gzip.open(f'../data/raw/{season}/play_by_play.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(play_by_play, f, indent=2)

    with gzip.open(f'../data/raw/{season}/shifts.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(shifts, f, indent=2)

if __name__ == "__main__":
    season = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    asyncio.run(main(season, start_date, end_date))
