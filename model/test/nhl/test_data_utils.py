import numpy as np
import pandas as pd
import pytest

from pandas.testing import assert_frame_equal
from common_test_functions import compare_mv_num_dict

from bayesbet.nhl.data_utils import get_unique_teams
from bayesbet.nhl.data_utils import get_teams_int_maps
from bayesbet.nhl.data_utils import model_vars_to_numeric
from bayesbet.nhl.data_utils import model_vars_to_string
from bayesbet.nhl.data_utils import model_ready_data


@pytest.fixture
def mock_games():
    game_pks = [1,2,3,4]
    game_types = ['P', 'R', 'R', 'R']
    home_teams = ['Team E', 'Team A', 'Team C', 'Team C']
    home_reg_scores = [0,1,2,3]
    home_fin_scores = [1,1,2,3]
    away_teams = ['Team F', 'Team B', 'Team D', 'Team A']
    away_reg_scores = [0,3,2,1]
    away_fin_scores = [0,3,3,1]

    games = pd.DataFrame({
        'game_pk':game_pks,
        'game_type':game_types,
        'home_team':home_teams,
        'home_reg_score': home_reg_scores,
        'home_fin_score': home_fin_scores,
        'away_team':away_teams,
        'away_reg_score': away_reg_scores,
        'away_fin_score': away_fin_scores,})
    return games

def test_get_unique_teams(mock_games):
    teams = get_unique_teams(mock_games)
    expected_teams = ['Team A', 'Team B', 'Team C', 'Team D']
    assert teams == expected_teams, "Did not get the expected unique teams!"

@pytest.fixture
def expected_teams_maps():
    teams = ['Team A', 'Team B', 'Team C']
    teams_to_int = {'Team A':0, 'Team B':1, 'Team C':2}
    int_to_teams = {0:'Team A', 1:'Team B', 2:'Team C'}
    return teams, teams_to_int, int_to_teams

@pytest.fixture
def expected_teams_maps_2():
    teams = ['Team A', 'Team B', 'Team C', 'Team D', 'Team E', 'Team F']
    teams_to_int = {'Team A':0, 'Team B':1, 'Team C':2, 'Team D':3, 'Team E':4, 'Team F':5}
    int_to_teams = {0:'Team A', 1:'Team B', 2:'Team C', 3:'Team D', 4:'Team E', 5:'Team F'}
    return teams, teams_to_int, int_to_teams

def test_get_teams_int_maps(expected_teams_maps):
    teams, expected_teams_to_int, expected_int_to_teams = expected_teams_maps
    teams_to_int, int_to_teams = get_teams_int_maps(teams)
    assert expected_teams_to_int == teams_to_int, "The teams_to_int map is wrong!"
    assert expected_int_to_teams == int_to_teams, "The int_to_teams map is wrong!"

@pytest.fixture
def expected_model_vars():
    mv_str_5 = {
        'i':['0.50000', '0.25000'],
        'h':['0.60000', '0.30000'],
        'teams': {
            'Team A': {'o':['0.10000', '0.05000'], 'd':['0.15000', '0.07500']},
            'Team B': {'o':['0.20000', '0.10000'], 'd':['0.25000', '0.12500']},
            'Team C': {'o':['0.30000', '0.15000'], 'd':['0.30000', '0.15000']},
        }
    }
    mv_str_3 = {
        'i':['0.500', '0.250'],
        'h':['0.600', '0.300'],
        'teams': {
            'Team A': {'o':['0.100', '0.050'], 'd':['0.150', '0.075']},
            'Team B': {'o':['0.200', '0.100'], 'd':['0.250', '0.125']},
            'Team C': {'o':['0.300', '0.150'], 'd':['0.300', '0.150']},
        }
    }
    mv_num = {
        'i':[0.5, 0.25],
        'h':[0.6, 0.3],
        'o':[np.array([0.1, 0.2, 0.3]), np.array([0.05, 0.1, 0.15])],
        'd':[np.array([0.15, 0.25, 0.3]), np.array([0.075, 0.125, 0.15])],
    }
    return mv_num, mv_str_3, mv_str_5

def test_model_vars_to_numeric(expected_teams_maps, expected_model_vars):
    teams, teams_to_int, int_to_teams = expected_teams_maps
    expected_mv_num, expected_mv_str_3, expected_mv_str_5 = expected_model_vars
    mv_num_3 = model_vars_to_numeric(expected_mv_str_3, teams_to_int)
    compare_mv_num_dict(mv_num_3, expected_mv_num)
    mv_num_5 = model_vars_to_numeric(expected_mv_str_5, teams_to_int)
    compare_mv_num_dict(mv_num_5, expected_mv_num)

def test_model_vars_to_string(expected_teams_maps, expected_model_vars):
    teams, teams_to_int, int_to_teams = expected_teams_maps
    expected_mv_num, expected_mv_str_3, expected_mv_str_5 = expected_model_vars
    mv_str_3 = model_vars_to_string(expected_mv_num, int_to_teams, decimals=3)
    assert mv_str_3 == expected_mv_str_3, "Model vars string dict with 3 decimal places does not match expected!"
    mv_str_5 = model_vars_to_string(expected_mv_num, int_to_teams, decimals=5)
    assert mv_str_5 == expected_mv_str_5, "Model vars string dict with 5 decimal places does not match expected!"

def test_model_ready_data(mock_games, expected_teams_maps_2):
    teams, teams_to_int, int_to_teams = expected_teams_maps_2
    data = model_ready_data(mock_games, teams_to_int)
    expected_data = pd.DataFrame({
        'idₕ': [4,0,2,2],
        'sₕ': [0,1,2,3],
        'idₐ': [5,1,3,0],
        'sₐ': [0,3,2,1],
        'hw': [True,False,False,True]
    })
    assert_frame_equal(data, expected_data)