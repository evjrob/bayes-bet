import logging
import os

import datetime as dt
import simplejson as json
import pandas as pd
import requests
from bayesbet.logger import get_logger


logger = get_logger(__name__)

# The NHL Statistics API URL
base_url = 'https://statsapi.web.nhl.com'

# Retrieves the JSON game data from the NHL stats API for a 
# selected date range.
def request_games_json(start_date, end_date):
    path = '/api/v1/schedule?startDate='+start_date+\
            '&endDate='+end_date+'&expand=schedule.linescore'
    response = requests.get(base_url + path)
    
    return response.json()

## Check if any games have been played on the specified date
def check_for_games(date=None):
    if date is None:
        date = dt.date.today().strftime('%Y-%m-%d')
    games_json = request_games_json(date, date)
    games_found = games_json['totalGames'] > 0
    
    return games_found

# Parses the games JSON data and extracts the relevant information
# into a pandas dataframe
def extract_game_data(games_json):
    games = pd.DataFrame(
        columns=['game_pk',
                 'game_date',
                 'season',
                 'game_type',
                 'game_state',
                 'home_team',
                 'home_reg_score',
                 'home_fin_score',
                 'away_team',
                 'away_reg_score',
                 'away_fin_score',
                 'win_type'])

    for date in games_json['dates']:
        game_date = date['date']
        for game in date['games']:
            game_pk = game['gamePk']
            season = game['season']
            game_type = game['gameType']
            game_state = game['status']['detailedState']

            home_team = game['teams']['home']['team']
            away_team = game['teams']['away']['team']
            home_team_name = home_team['name']
            away_team_name = away_team['name']

            detailed_score_data = game['linescore']
            home_fin_score = detailed_score_data['teams']['home']['goals']
            away_fin_score = detailed_score_data['teams']['away']['goals']

            periods_list = detailed_score_data['periods']
            home_reg_score = 0
            away_reg_score = 0
            win_type = 'REG'
            for period in periods_list:
                period_type = period['periodType']
                if period_type == 'REGULAR':
                    home_reg_score += period['home']['goals']
                    away_reg_score += period['away']['goals']
                if period_type == 'OVERTIME':
                    win_type = 'OT'
            if detailed_score_data['hasShootout'] == True:
                win_type == 'SO'

            games = games.append(
                {'game_pk': game_pk,
                 'game_date': game_date,
                 'season': season,
                 'game_type': game_type,
                 'game_state': game_state,
                 'home_team': home_team_name,
                 'home_reg_score': home_reg_score,
                 'home_fin_score': home_fin_score,
                 'away_team': away_team_name,
                 'away_reg_score': away_reg_score,
                 'away_fin_score': away_fin_score,
                 'win_type': win_type},
                ignore_index=True)

    return games

def get_min_game_date(games, min_reg_game_days):
    game_days = games.copy()
    game_days = game_days[game_days['game_type'] == 'R']
    game_days = game_days['game_date'].sort_values(ascending=False)
    game_days = game_days.unique()
    min_game_date = game_days[min_reg_game_days]
    
    return min_game_date

def fetch_nhl_data_by_dates(start_date, end_date):
    """ 
    Retrieves data from the NHL stats API and loads it into a dataframe.
    """
    logger.info(f'Retrieving NHL data for {start_date} to {end_date}')

    games_json = request_games_json(start_date, end_date)

    # Convert JSON to pandas for ingestion by model
    game_data = extract_game_data(games_json)

    logger.info('NHL game data successfully retrieved from API')

    return game_data

def fetch_recent_nhl_data(min_reg_game_days):
    """ 
    Retrieves data from the NHL stats API and loads it into a dataframe.
    """
    today = dt.date.today()
    start_date = (today - dt.timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    game_data = fetch_nhl_data_by_dates(start_date, end_date)
    
    # Filter results to the minimum number of regulation game days
    min_game_date = get_min_game_date(game_data, min_reg_game_days)
    game_data = game_data[game_data['game_date'] >= min_game_date].copy()

    logger.info(f'Games filtered to all games since {min_game_date}')

    return game_data

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    data = fetch_recent_nhl_data(2)
    print(data)