import logging
import os
import numpy as np
import pandas as pd

from bayesbet.logger import get_logger


logger = get_logger(__name__)

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
