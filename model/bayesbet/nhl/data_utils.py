import logging
import os
import numpy as np
import pandas as pd

from bayesbet.logger import get_logger


logger = get_logger(__name__)


game_type_mapping = {
    1: 'Pr',
    2: 'R',
    3: 'P',
    4: 'A',
    6: 'Other',
    7: 'Other',
    8: 'Other',
    12: 'Other',
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

        if 'score' in home_team and 'score' in away_team:
            home_fin_score = home_team['score']
            away_fin_score = away_team['score']
        else:
            home_fin_score = 0
            away_fin_score = 0

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

    assert not (
        games["game_type"].isin(["R", "P"]) 
        & (games["home_team"].isnull() | games["away_team"].isnull())
    ).any()

    date_metadata = {
        "previous_game_date": previous_game_date,
        "next_game_date": next_game_date,
    }

    return games, date_metadata


def get_unique_teams(game_data):
    # We only want teams that play in the regular season
    reg_season_data = game_data[game_data['game_type'] == 'R']
    home_teams = reg_season_data['home_team']
    away_teams = reg_season_data['away_team']
    teams = list(pd.concat([home_teams, away_teams]).sort_values().unique())

    return teams

def get_teams_int_maps(teams):
    teams_to_int = {}
    int_to_teams = {}
    for i,t in enumerate(teams):
        teams_to_int[t] = i
        int_to_teams[i] = t
    return teams_to_int, int_to_teams

def model_vars_to_numeric(mv_in, teams_to_int):
    mv = {}
    n_teams = len(teams_to_int)
    default_μ = 0.0
    default_σ = 0.15
    mv['i'] = [float(s) for s in mv_in['i']]
    mv['h'] = [float(s) for s in mv_in['h']]
    mv['o'] = [np.array([default_μ]*n_teams), np.array([default_σ]*n_teams)]
    mv['d'] = [np.array([default_μ]*n_teams), np.array([default_σ]*n_teams)]
    for t,n in teams_to_int.items():
        if t in mv_in['teams'].keys():
            mv['o'][0][n] = float(mv_in['teams'][t]['o'][0])
            mv['o'][1][n] = float(mv_in['teams'][t]['o'][1])
            mv['d'][0][n] = float(mv_in['teams'][t]['d'][0])
            mv['d'][1][n] = float(mv_in['teams'][t]['d'][1])
        else:
            logger.warning(f'Did not find team {t} in model_vars! Defaulting to μ={default_μ} and σ={default_σ}!')

    return mv

def model_vars_to_string(mv_in, int_to_teams, decimals=5):
    mv = {}
    precision = f'.{decimals}f'
    mv['i'] = [f'{n:{precision}}' for n in mv_in['i']]
    mv['h'] = [f'{n:{precision}}' for n in mv_in['h']]
    mv['teams'] = {}
    for n,t in int_to_teams.items():
        n = int(n)
        o_μ = mv_in['o'][0][n]
        o_σ = mv_in['o'][1][n]
        d_μ = mv_in['d'][0][n]
        d_σ = mv_in['d'][1][n]
        mv['teams'][t] = {}
        mv['teams'][t]['o'] = [f'{o_μ:{precision}}',  f'{o_σ:{precision}}']
        mv['teams'][t]['d'] = [f'{d_μ:{precision}}',  f'{d_σ:{precision}}']
    return mv

def model_ready_data(game_data, teams_to_int):
    model_data = pd.DataFrame()
    model_data['idₕ'] = game_data['home_team'].replace(teams_to_int)
    model_data['sₕ'] = game_data['home_reg_score']
    model_data['idₐ'] = game_data['away_team'].replace(teams_to_int)
    model_data['sₐ'] = game_data['away_reg_score']
    model_data['hw'] = game_data['home_fin_score'] > game_data['away_fin_score']

    return model_data
