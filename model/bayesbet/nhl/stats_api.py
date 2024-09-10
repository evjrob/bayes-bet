import logging
import os

import datetime as dt
import simplejson as json
import pandas as pd
import requests
from bayesbet.logger import get_logger


logger = get_logger(__name__)

# The NHL Statistics API URL
base_url = 'https://api-web.nhle.com'


# Retrieves the JSON game data from the NHL stats API for a 
# selected date range.
def request_games_json(date):
    path = '/v1/score/'+date
    response = requests.get(base_url + path)
    
    return response.json()

# Retrieves the play-by-play data from the NHL stats API for a given game id
def request_play_by_play_json(game_id):
    path = f'/v1/gamecenter/{game_id}/play-by-play'
    response = requests.get(base_url + path)
    
    return response.json()

# Retrieves the shift data from the NHL stats API for a given game id
def request_shifts_json(game_id):
    path = f"/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id} and (duration != '00:00' and typeCode = 517)'"
    response = requests.get(base_url + path)
    
    return response.json()    

## Check if any games have been played on the specified date
def check_for_games(date=None):
    if date is None:
        date = dt.date.today().strftime('%Y-%m-%d')
    games_json = request_games_json(date, date)
    games_found = games_json['totalGames'] > 0
    
    return games_found

def get_min_game_date(games, min_reg_game_days):
    game_days = games.copy()
    game_days = game_days[game_days['game_type'] == 'R']
    game_days = game_days['game_date'].sort_values(ascending=False)
    game_days = game_days.unique()
    min_game_date = game_days[min_reg_game_days]
    
    return min_game_date


def get_season_start_date(season):
    """ 
    Finds the regular season start date of the requested season.
    """
    path = '/v1/standings-season/'
    response = requests.get(base_url + path)
    seasons_json = response.json()
    seasons = {s["id"]:s["standingsStart"] for s in seasons_json["seasons"]}

    return seasons[season]
