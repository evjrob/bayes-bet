import logging
import os

import datetime as dt
import simplejson as json
import pandas as pd
import aiohttp
import asyncio
from bayesbet.logger import get_logger


logger = get_logger(__name__)

# The NHL Statistics API URL
base_url = 'https://api-web.nhle.com'
stats_url = 'https://api.nhle.com/stats/rest/en'


# Retrieves the JSON team data from the NHL stats API. Contains all teams,
# current and historic.
async def request_teams_json(session):
    path = '/team'
    async with session.get(stats_url + path) as response:
        return await response.json()
    
# Retrieves the JSON player data from the NHL stats API.
async def request_player_json(session, player_id):
    path = f'/v1/player/{player_id}/landing'
    async with session.get(base_url + path) as response:
        # Not all player_id have a landing page. Mostly this is for AHL players
        # like Kevin Sundher, who played in some preseason games ut apparently
        # lack the noteriety for a dedicated page.
        try:
            return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                print(f"Player id {player_id} not found")
                return None
            else:
                raise e

# Retrieves the JSON game data from the NHL stats API for a 
# selected date range.
async def request_games_json(session, date):
    path = '/v1/score/'+date
    async with session.get(base_url + path) as response:
        return await response.json()

# Retrieves the play-by-play data from the NHL stats API for a given game id
async def request_play_by_play_json(session, game_id):
    path = f'/v1/gamecenter/{game_id}/play-by-play'
    async with session.get(base_url + path) as response:
        return await response.json()

# Retrieves the shift data from the NHL stats API for a given game id
async def request_shifts_json(session, game_id):
    path = f"/shiftcharts?cayenneExp=gameId={game_id} and (duration != '00:00' and typeCode = 517)"
    async with session.get(stats_url + path) as response:
        return await response.json()    

## Check if any games have been played on the specified date
async def check_for_games(session, date=None):
    if date is None:
        date = dt.date.today().strftime('%Y-%m-%d')
    games_json = await request_games_json(session, date)
    games_found = games_json['totalGames'] > 0
    
    return games_found

def get_min_game_date(games, min_reg_game_days):
    game_days = games.copy()
    game_days = game_days[game_days['game_type'] == 'R']
    game_days = game_days['game_date'].sort_values(ascending=False)
    game_days = game_days.unique()
    min_game_date = game_days[min_reg_game_days]
    
    return min_game_date


async def get_season_start_date(session, season):
    """ 
    Finds the regular season start date of the requested season.
    """
    path = '/v1/standings-season/'
    async with session.get(base_url + path) as response:
        seasons_json = await response.json()
    seasons = {s["id"]:s["standingsStart"] for s in seasons_json["seasons"]}

    return seasons[season]
