import logging
import os
import numpy as np


logger = logging.getLogger(__name__)

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
        mv['o'][0][n] = float(mv_in['teams'][t]['o'][0])
        mv['o'][1][n] = float(mv_in['teams'][t]['o'][1])
        mv['d'][0][n] = float(mv_in['teams'][t]['d'][0])
        mv['d'][1][n] = float(mv_in['teams'][t]['d'][1])
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