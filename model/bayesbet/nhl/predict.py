import logging
import os

import json
from math import factorial, exp, sqrt, pi
import numpy as np
from scipy.integrate import quad, dblquad

from bayesbet.logger import get_logger


logger = get_logger(__name__)
t_before_shootout = 5.0/60.0    # 5 minute shootout, divided by regulation time

def bayesian_poisson_pdf(μ, σ, max_y=10):
    def integrand(x, y, σ, μ):
        pois = (np.exp(x)**y)*np.exp(-np.exp(x))/factorial(y)
        norm = np.exp(-0.5*((x-μ)/σ)**2.0)/(σ * sqrt(2.0*pi))
        return  pois * norm

    lwr = -3.0
    upr = 5.0

    y = np.arange(0,max_y)
    p = []
    for yi in y:
        I = quad(integrand, lwr, upr, args=(yi,σ,μ))
        p.append(I[0])
    p.append(1.0 - sum(p))
    
    return p

def bayesian_bernoulli_win_pdf(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
    def dblintegrand(y, x, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
        normₕ = np.exp(-0.5*((x-log_λₕ_μ)/log_λₕ_σ)**2)/(log_λₕ_σ * sqrt(2*pi))
        normₐ = np.exp(-0.5*((y-log_λₐ_μ)/log_λₐ_σ)**2)/(log_λₐ_σ * sqrt(2*pi))
        λₕ = np.exp(x)
        λₐ = np.exp(y)
        p_dydx = normₐ*normₕ*λₕ/(λₕ + λₐ)
        return p_dydx

    lwr = -3.0
    upr = 5.0

    I = dblquad(dblintegrand, lwr, upr, lwr, upr, args=(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ))
    p = I[0]

    return p

def bayesian_goal_within_time(t, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
    def dblintegrand(y, x, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
        normₕ = np.exp(-0.5*((x-log_λₕ_μ)/log_λₕ_σ)**2)/(log_λₕ_σ * sqrt(2*pi))
        normₐ = np.exp(-0.5*((y-log_λₐ_μ)/log_λₐ_σ)**2)/(log_λₐ_σ * sqrt(2*pi))
        λₕ = np.exp(x)
        λₐ = np.exp(y)
        p = normₐ*normₕ*(1 - np.exp(-1*(λₕ*t + λₐ*t)))
        return p

    lwr = -3.0
    upr = 5.0

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
        game_pred['home_team'] = game['home_team']
        game_pred['away_team'] = game['away_team']
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
        log_λₕ_σ = np.sqrt(i_σ**2 + h_σ**2 + oₕ_σ**2 + dₐ_σ**2)
        log_λₐ_μ = i_μ + oₐ_μ - dₕ_μ
        log_λₐ_σ = np.sqrt(i_σ**2 + oₐ_σ**2 + dₕ_σ**2)
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
                        p_so_win = 1.0 - p_ot_win
                    else:
                        p_ot_win = 1.0
                        p_so_win = 0.0
                    pₕ_ot = bayesian_bernoulli_win_pdf(log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ)
                    pₐ_ot = 1.0 - pₕ_ot
                    home_ot_win_p += pₕ_ot * p_ot_win * p
                    home_so_win_p += pₕ_ot * p_so_win * p
                    away_ot_win_p += pₐ_ot * p_ot_win * p
                    away_so_win_p += pₐ_ot * p_so_win * p
        win_percentages = [home_reg_win_p, home_ot_win_p, home_so_win_p, away_reg_win_p, away_ot_win_p, away_so_win_p]
        game_pred['WinPercentages'] = [f'{wp:{precision}}' for wp in win_percentages]
        game_predictions_list.append(game_pred)
    return game_predictions_list

if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    #print(bayesian_poisson_pdf(1.75, 0.15))
    #item = most_recent_dynamodb_item('nhl', '2020-07-26')
    #print(item)