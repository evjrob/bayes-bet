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

game_type_mapping = {
    1: 'Pr',
    2: 'R',
    3: 'P',
    4: 'A',
}

game_state_mapping = {
    "OFF": "Final",
    "FINAL": "Final",
    "FUT": "Future",
}

team_abbrevs = {
    'Anaheim Ducks':'ANA',
    'Arizona Coyotes':'ARI',
    'Boston Bruins':'BOS',
    'Buffalo Sabres':'BUF',
    'Calgary Flames':'CGY',
    'Carolina Hurricanes':'CAR',
    'Chicago Blackhawks':'CHI',
    'Colorado Avalanche':'COL',
    'Columbus Blue Jackets':'CBJ',
    'Dallas Stars':'DAL',
    'Detroit Red Wings':'DET',
    'Edmonton Oilers':'EDM',
    'Florida Panthers':'FLA',
    'Los Angeles Kings':'LAK',
    'Minnesota Wild':'MIN',
    'Montréal Canadiens':'MTL',
    'Nashville Predators':'NSH',
    'New Jersey Devils':'NJD',
    'New York Islanders':'NYI',
    'New York Rangers':'NYR',
    'Ottawa Senators':'OTT',
    'Philadelphia Flyers':'PHI',
    'Pittsburgh Penguins':'PIT',
    'San Jose Sharks':'SJS',
    'Seattle Kraken':'SEA',
    'St. Louis Blues':'STL',
    'Tampa Bay Lightning':'TBL',
    'Toronto Maple Leafs':'TOR',
    'Vancouver Canucks':'VAN',
    'Vegas Golden Knights':'VGK',
    'Washington Capitals':'WSH',
    'Winnipeg Jets':'WPG',
}
team_names = {v:k for k,v in team_abbrevs.items()}

# Retrieves the JSON game data from the NHL stats API for a 
# selected date range.
def request_games_json(date):
    path = '/v1/score/'+date
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
    previous_game_date = games_json["prevDate"]
    next_game_date = games_json["nextDate"]
    games = []

    for game in games_json['games']:
        game_date = game['gameDate']
        game_pk = game['id']
        season = game['season']
        game_type = game['gameType']
        game_state = game['gameState']

        home_team = game['homeTeam']
        away_team = game['awayTeam']
        home_team_name = home_team['abbrev']
        away_team_name = away_team['abbrev']

        home_fin_score = home_team['score']
        away_fin_score = away_team['score']

        home_reg_score = home_fin_score
        away_reg_score = away_fin_score

        if "gameOutcome" in game:
            win_type = game["gameOutcome"]["lastPeriodType"]
            if win_type in ["OT", "SO"]:
                if home_fin_score > away_fin_score:
                    home_reg_score -= 1
                elif away_fin_score > home_reg_score:
                    away_reg_score -= 1
        else:
            win_type = "NA"

        games.append(
            {
                'game_pk': game_pk,
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
                'win_type': win_type
            }
        )

    games = pd.DataFrame(games)
    games["game_type"] = games["game_type"].map(game_type_mapping)
    games["game_state"] = games["game_state"].map(game_state_mapping)
    games["home_team"] = games["home_team"].map(team_names)
    games["away_team"] = games["away_team"].map(team_names)

    date_metadata = {
        "previous_game_date": previous_game_date,
        "next_game_date": next_game_date,
    }

    return games, date_metadata

def get_min_game_date(games, min_reg_game_days):
    game_days = games.copy()
    game_days = game_days[game_days['game_type'] == 'R']
    game_days = game_days['game_date'].sort_values(ascending=False)
    game_days = game_days.unique()
    min_game_date = game_days[min_reg_game_days]
    
    return min_game_date

def fetch_nhl_data_by_date(date):
    """ 
    Retrieves data from the NHL stats API and loads it into a dataframe.
    """
    logger.info(f'Retrieving NHL data for {date}')

    games_json = request_games_json(date)

    # Convert JSON to pandas for ingestion by model
    game_data, date_metadata = extract_game_data(games_json)

    logger.info('NHL game data successfully retrieved from API')

    return game_data, date_metadata

def fetch_recent_nhl_data(min_reg_game_days):
    """ 
    Retrieves data from the NHL stats API and loads it into a dataframe.
    """
    today = dt.date.today()
    start_date = (today - dt.timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    full_game_data = []
    game_data, date_metadata = fetch_nhl_data_by_date(start_date)
    next_game_date = date_metadata["next_game_date"]
    while next_game_date <= end_date:
        game_data, date_metadata = fetch_nhl_data_by_date(date)
        next_game_date = date_metadata["next_game_date"]
        full_game_data.append(game_data)
    game_data = pd.concatenate(full_game_data)
    
    # Filter results to the minimum number of regulation game days
    min_game_date = get_min_game_date(game_data, min_reg_game_days)
    game_data = game_data[game_data['game_date'] >= min_game_date].copy()

    logger.info(f'Games filtered to all games since {min_game_date}')

    return game_data

def get_season_start_date(season):
    """ 
    Finds the regular season start date of the requested season.
    """
    path = '/v1/standings-season/'
    response = requests.get(base_url + path)
    seasons_json = response.json()
    seasons = {s["id"]:s["standingsStart"] for s in seasons_json["seasons"]}

    return seasons[season]


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    data = fetch_recent_nhl_data(2)
    print(data)