import logging
import os
import numpy as np
import pandas as pd
import datetime as dt

from query_api import check_for_games, fetch_recent_nhl_data, fetch_nhl_data_by_dates
from results import most_recent_dynamodb_item, model_vars_to_numeric, model_vars_to_string, \
    get_teams_int_maps, create_dynamodb_item, put_dynamodb_item
from model import model_ready_data, model_update

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

framework = 'PyMC3'
model_version = 'v2.1'
fattening_factor = 1.02  # Expand the posteriors by this amount before using as priors
f_thresh = 0.075         # A cap on team variable standard deviation to prevent blowup
window_size = 1          # The number previous game days used in each iteration
delta_sigma = 0.001      # The standard deviaton of the random walk variables
metadata = {
    'framework': framework,
    'model_version': model_version,
    'fattening_factor': str(fattening_factor),
    'window_size': str(window_size),
    'delta_sigma': str(delta_sigma)
}


def get_unique_teams(game_data):
    # We only want teams that play in the regular season
    reg_season_data = game_data[game_data['game_type'] == 'R']
    home_teams = reg_season_data['home_team']
    away_teams = reg_season_data['away_team']
    teams = list(pd.concat([home_teams, away_teams]).sort_values().unique())
    
    return teams

def init_model(games, teams_to_int, f, f_thresh):
    obs_data = model_ready_data(games, teams_to_int)

    n_teams = len(teams_to_int)
    init_priors = {
        'h': [0.2, 0.1],
        'i': [1.0, 0.1],
        'o': [np.array([0.0] * n_teams), np.array([0.2] * n_teams)],
        'd': [np.array([0.0] * n_teams), np.array([0.2] * n_teams)]
    }

    posteriors = model_update(obs_data, init_priors, n_teams, f, f_thresh, 0.25)

    #create_dynamodb_item(date, posteriors, int_to_teams, teams_to_int, metadata)

    return posteriors

def initialize():
    start_date = '2017-08-01'
    end_date = '2018-08-01'
    games = fetch_nhl_data_by_dates(start_date, end_date)
    games = games[games['game_type'] != 'A'] # No All Star games
    teams = get_unique_teams(games)
    teams_to_int, int_to_teams = get_teams_int_maps(teams)
    posteriors = init_model(games, teams_to_int, 1.0, 0.25)
    record = create_dynamodb_item(end_date, posteriors, int_to_teams, teams_to_int, metadata)
    put_dynamodb_item(record)
    return

def main():
    today_dt = dt.date.today()
    today = today_dt.strftime('%Y-%m-%d')
    last_pred = most_recent_dynamodb_item('nhl', today)
    last_pred_date = last_pred['PredictionDate']
    last_pred_dt = dt.date.fromisoformat(last_pred_date)
    logger.info(f'Most recent prediction is from {last_pred_date}')
    start_date = (last_pred_dt - dt.timedelta(days=365)).strftime('%Y-%m-%d')

    games = fetch_nhl_data_by_dates(start_date, today)
    games = games[games['game_type'] != 'A'] # No All Star games
    
    teams = get_unique_teams(games)
    teams_to_int, int_to_teams = get_teams_int_maps(teams)
    n_teams = len(teams)

    # Get last_pred posteriors to use as priors
    priors = last_pred['ModelVariables']
    priors = model_vars_to_numeric(priors, teams_to_int)

    # Drop games with non-nhl teams (usually preseason exhibition games)
    valid_rows = (games['home_team'].isin(teams) & games['away_team'].isin(teams))
    games = games[valid_rows]
    
    # Update scores in the last prediction
    updated_last_pred = last_pred.copy()
    if 'GamePredictions' in updated_last_pred.keys():
        for g in updated_last_pred['GamePredictions']:
            gpk = g['game_pk']
            game_row = games[games['game_pk'] == gpk]
            home_fin_score = str(game_row['home_fin_score'].values[0])
            away_fin_score = str(game_row['away_fin_score'].values[0])
            g['score']['home'] = home_fin_score
            g['score']['away'] = away_fin_score
        put_dynamodb_item(updated_last_pred)
        logger.info(f'Updated scores for item in bayes-bet-table with League=nhl and date={last_pred_date}')

    # Backfill missing predictions
    game_dates = games['game_date'].drop_duplicates()
    new_pred_dates = [gd for gd in game_dates if gd > last_pred_date]
    if len(new_pred_dates) == 0:
        logger.info(f'No new games to predict on.')
    for gd in new_pred_dates:
        logger.info(f'Generating new NHL model predictions for {gd}')
        # Get the most recent game date played
        prev_gd = max([gd2 for gd2 in game_dates if gd2 < gd])
        obs_data = model_ready_data(games[games['game_date'] == prev_gd], teams_to_int)
        posteriors = model_update(obs_data, priors, n_teams, fattening_factor, f_thresh, delta_sigma)
        priors = posteriors.copy()
        pred_games = games[games['game_date'] == gd]
        record = create_dynamodb_item(gd, posteriors, int_to_teams, teams_to_int, metadata, games_to_predict=pred_games)
        put_dynamodb_item(record)
        logger.info(f'Added prediction to bayes-bet-table with League=nhl and date={gd}')
    
    # Backfill model performance

    return

if __name__ == "__main__":
    main()