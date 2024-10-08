import boto3
import simplejson as json
import logging
import os
import numpy as np
import pandas as pd
import datetime as dt

from bayesbet.logger import get_logger
from bayesbet.nhl.data_model import GamePrediction, PredictionRecord


logger = get_logger(__name__)


def single_prediction_log_loss(game_prediction: GamePrediction) -> float:
    home_win_probability = game_prediction.win_percentages.home.total_win_probability()
    home_win_occurred = game_prediction.outcome.home_win()
    log_loss = (
        home_win_occurred * np.log(home_win_probability) 
        + (1 - home_win_occurred) * np.log(1 - home_win_probability)
    )
    return log_loss


def single_prediction_correct(game_prediction: GamePrediction) -> bool:
    home_win_predicted = (
        game_prediction.win_percentages.home.total_win_probability() >= 0.5
    )
    home_win_occurred = game_prediction.outcome.home_win()
    return home_win_predicted == home_win_occurred


def log_loss(game_predictions: list[GamePrediction]) -> float:
    log_losses = [single_prediction_log_loss(gp) for gp in game_predictions]
    return (-1 / len(log_losses)) * sum(log_losses)


def accuracy(game_predictions: list[GamePrediction]) -> float:
    prediction_correct = [single_prediction_correct(gp) for gp in game_predictions]
    return sum(prediction_correct) / len(prediction_correct)


def update_scores(last_pred, games):
    updated_last_pred = last_pred.copy()
    last_pred_date = last_pred.prediction_date
    for g in updated_last_pred.predictions:
        gpk = g.game_pk
        game_row = games[games['game_pk'] == gpk]
        if game_row.shape[0] == 0:
            logger.info(f'Failed to update game scores on {last_pred_date} with game_pk {gpk}.')
            continue
        # Only update the score if the game wasn't postponed
        if game_row['game_state'].values[0] != 'Postponed':
            home_fin_score = str(game_row['home_fin_score'].values[0])
            away_fin_score = str(game_row['away_fin_score'].values[0])
            if home_fin_score != '0' or away_fin_score != '0':
                g.outcome.home_score = home_fin_score
                g.outcome.away_score = away_fin_score

    return updated_last_pred

def prediction_performance(db_records, games, ws=14):
    # Make the db_records into a pandas dataframe
    model_pred_perf = []
    for r in db_records:
            date = r.prediction_date
            game_preds = r.predictions
            for g in game_preds:
                game_pk = g.game_pk
                hg = g.outcome.home_score
                ag = g.outcome.away_score
                if hg != '-' and ag != '-':
                    hg = int(hg)
                    ag = int(ag)
                    hw = hg > ag
                    pred_hw = g.win_percentages.home.total_win_probability()
                    model_pred_perf.append([date, game_pk, hg, ag, hw, pred_hw])

    model_preds = pd.DataFrame(
        data=model_pred_perf, 
        columns=['date', 'game_pk', 'home_goals', 'away_goals', 'home_win', 'home_win_pred'])
    model_preds = model_preds.sort_values(['date', 'game_pk'])

    # For each game date, compute the cumulative and rolling accuracies and log losses
    game_dates = model_preds['date'].unique().tolist() 
    model_perf = []
    for d in game_dates:
        upr = d
        if d >= game_dates[min(ws, len(game_dates)-1)]:
            lwr = game_dates[max(game_dates.index(d) - ws, 0)]
        else:
            lwr = game_dates[0]
        
        cum_preds = model_preds[model_preds['date'] <= upr]
        total_games = cum_preds.shape[0]
        cum_acc = (cum_preds['home_win'] == (cum_preds['home_win_pred'] >= 0.5)).mean()
        cum_ll = -1 * (cum_preds['home_win'] * np.log(cum_preds['home_win_pred']) + \
            (1 - cum_preds['home_win']) * np.log(1 - cum_preds['home_win_pred'])).mean()
        
        rolling_idx = (model_preds['date'] >= lwr) & (model_preds['date'] <= upr)
        rolling_preds = model_preds[rolling_idx]
        rolling_acc = (rolling_preds['home_win'] == (rolling_preds['home_win_pred'] >= 0.5)).mean()
        rolling_ll = -1 * (rolling_preds['home_win'] * np.log(rolling_preds['home_win_pred']) + \
            (1 - rolling_preds['home_win']) * np.log(1 - rolling_preds['home_win_pred'])).mean()
        model_perf.append([upr, total_games, cum_acc, rolling_acc, cum_ll, rolling_ll])

    model_perf = pd.DataFrame(
        data=model_perf,
        columns=[
            'prediction_date',
            'total_games',
            'cumulative_accuracy',
            'rolling_accuracy',
            'cumulative_log_loss',
            'rolling_log_loss',
        ],
    )
    model_perf = model_perf.reset_index(drop=True)

    return model_perf