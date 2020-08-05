import logging
import os

import json
import boto3
from boto3.dynamodb.conditions import Key
from math import factorial, exp, sqrt, pi
import numpy as np
from scipy.integrate import quad, dblquad


logger = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('bayes-bet-table')

t_before_shootout = 5.0/60.0    # 5 minute shootout, divided by regulation time

def most_recent_dynamodb_item(hash_key, date):
    logger.info(f'Get most recent item from bayes-bet-table with League={hash_key} and date={date}')
    response = table.query(
        Limit = 1,
        ScanIndexForward = False,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq(hash_key) & Key('PredictionDate').lte(date)
    )
    item_count = len(response['Items'])
    capacity_units = response['ConsumedCapacity']['CapacityUnits']
    logger.info(f'Query consumed {capacity_units} capacity units')
    if item_count > 0:
        most_recent_item = response['Items'][0]
    else:
        most_recent_item = None
    
    return most_recent_item

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

def bayesian_poisson_pdf(μ, σ, max_y=15):
    def integrand(x, y, σ, μ):
        pois = exp(x*y)*exp(-exp(x))/factorial(y)
        norm = exp(-0.5*((x-μ)/σ)**2)/(σ * sqrt(2*pi))
        return  pois * norm

    lwr = -10
    upr = 10

    y = np.arange(0,max_y)
    p = []
    for yi in y:
        I = quad(integrand, lwr, upr, args=(yi,σ,μ))
        p.append(I[0])
    p.append(1 - sum(p))
    
    return p

def bayesian_bernoulli_win_pdf(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
    def dblintegrand(y, x, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
        normₕ = exp(-0.5*((x-log_λₕ_μ)/log_λₕ_σ)**2)/(log_λₕ_σ * sqrt(2*pi))
        normₐ = exp(-0.5*((y-log_λₐ_μ)/log_λₐ_σ)**2)/(log_λₐ_σ * sqrt(2*pi))
        λₕ = exp(x)
        λₐ = exp(y)
        p_dydx = normₐ*normₕ*λₕ/(λₕ + λₐ)
        return p_dydx

    lwr = -10
    upr = 10

    I = dblquad(dblintegrand, lwr, upr, lwr, upr, args=(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ))
    p = I[0]

    return p

def bayesian_goal_within_time(t, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
    def dblintegrand(y, x, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
        normₕ = exp(-0.5*((x-log_λₕ_μ)/log_λₕ_σ)**2)/(log_λₕ_σ * sqrt(2*pi))
        normₐ = exp(-0.5*((y-log_λₐ_μ)/log_λₐ_σ)**2)/(log_λₐ_σ * sqrt(2*pi))
        λₕ = exp(x)
        λₐ = exp(y)
        p = normₐ*normₕ*(1 - exp(-1*(λₕ*t + λₐ*t)))
        return p

    lwr = -10
    upr = 10

    I = dblquad(dblintegrand, lwr, upr, lwr, upr, args=(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ))
    p = I[0]

    return p

def game_predictions(games, posteriors, teams_to_int, decimals=5):
    precision = f'.{decimals}f'
    game_predictions_list = []
    for _, game in games.iterrows():
        logger.info(f'Generating predictions for game_pk {game["game_pk"]}')
        game_pred = {}
        game_pred['game_pk'] = game['game_pk']
        game_pred['score'] = {}
        if game['game_state'] =='Final':
            game_pred['score']['home'] = str(game['home_fin_score'])
            game_pred['score']['away'] = str(game['away_fin_score'])
        else:
            game_pred['score']['home'] = '-'
            game_pred['score']['away'] = '-'
        idₕ = teams_to_int[game['home_team']]
        idₐ = teams_to_int[game['away_team']]
        i_μ = posteriors['i'][0]
        i_σ = posteriors['i'][1]
        h_μ = posteriors['h'][0]
        h_σ = posteriors['h'][1]
        oₕ_μ = posteriors['o'][0][idₕ]
        oₕ_σ = posteriors['o'][1][idₕ]
        oₐ_μ = posteriors['o'][0][idₐ]
        oₐ_σ = posteriors['o'][1][idₐ]
        dₕ_μ = posteriors['d'][0][idₕ]
        dₕ_σ = posteriors['d'][1][idₕ]
        dₐ_μ = posteriors['d'][0][idₐ]
        dₐ_σ = posteriors['d'][1][idₐ]
        # Normal(μ₁,σ₁²) + Normal(μ₂,σ₂²) = Normal(μ₁ + μ₂, σ₁² + σ₂²)
        log_λₕ_μ = i_μ + h_μ + oₕ_μ - dₐ_μ
        log_λₕ_σ = i_σ**2 + h_σ**2 + oₕ_σ**2 + dₐ_σ**2
        log_λₐ_μ = i_μ + oₐ_μ - dₕ_μ
        log_λₐ_σ = i_σ**2 + oₐ_σ**2 + dₕ_σ**2
        home_score_pdf = bayesian_poisson_pdf(log_λₕ_μ, log_λₕ_σ)
        away_score_pdf = bayesian_poisson_pdf(log_λₐ_μ, log_λₐ_σ)
        game_pred['ScoreProbabilities'] = {
            'home': [f'{s:{precision}}' for s in home_score_pdf],
            'away': [f'{s:{precision}}' for s in away_score_pdf]
        }
        home_reg_win_p = 0.0
        home_ot_win_p = 0.0
        home_so_win_p = 0.0
        away_reg_win_p = 0.0
        away_ot_win_p = 0.0
        away_so_win_p = 0.0
        for sₕ, pₕ in enumerate(home_score_pdf):
            for sₐ, pₐ in enumerate(away_score_pdf):
                p = pₕ * pₐ
                if sₕ > sₐ:
                    home_reg_win_p += p
                elif sₐ > sₕ:
                    away_reg_win_p += p
                else:
                    if game['game_type'] != 'P':
                        p_ot_win = bayesian_goal_within_time(t_before_shootout, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ)
                        p_so_win = 1 - p_ot_win
                    else:
                        p_ot_win = 1.0
                        p_so_win = 0.0
                    pₕ_ot = bayesian_bernoulli_win_pdf(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ)
                    pₐ_ot = 1 - pₕ_ot
                    home_ot_win_p += pₕ_ot * p_ot_win
                    home_so_win_p += pₕ_ot * p_so_win
                    away_ot_win_p += pₐ_ot * p_ot_win
                    home_so_win_p += pₕ_ot * p_so_win
        win_percentages = [home_reg_win_p, home_ot_win_p, home_so_win_p, away_reg_win_p, away_ot_win_p, away_so_win_p]
        game_pred['WinPercentages'] = [f'{wp:{precision}}' for wp in win_percentages]
        game_predictions_list.append(game_pred)
    return game_predictions_list

def create_dynamodb_item(pred_date, posteriors, int_to_teams, teams_to_int, metadata, games_to_predict=None):
    item = {'League':'nhl', 'PredictionDate':pred_date}
    if games_to_predict is not None:
        game_preds = game_predictions(games_to_predict, posteriors, teams_to_int)
        item['GamePredictions'] = game_preds
    model_vars = model_vars_to_string(posteriors, int_to_teams)
    item['ModelVariables'] = model_vars
    item['ModelMetadata'] = metadata

    return item

def put_dynamodb_item(item):
    response = table.put_item(Item=item)
    return response

if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    #print(bayesian_poisson_pdf(1.75, 0.15))
    item = most_recent_dynamodb_item('nhl', '2020-07-26')
    #print(item)