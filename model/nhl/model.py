import logging
import os

import numpy as np
import pandas as pd
import pymc3 as pm
import theano.tensor as tt
import theano
from scipy.stats import norm


logger = logging.getLogger(__name__)

def model_ready_data(game_data, teams_to_int):
    model_data = pd.DataFrame()
    model_data['idₕ'] = game_data['home_team'].replace(teams_to_int)
    model_data['sₕ'] = game_data['home_reg_score']
    model_data['idₐ'] = game_data['away_team'].replace(teams_to_int)
    model_data['sₐ'] = game_data['away_reg_score']
    model_data['hw'] = game_data['home_fin_score'] > game_data['away_fin_score']

    return model_data

def get_model_posteriors(trace, n_teams):
    posteriors = {}
    h_μ, h_σ = norm.fit(trace['h'])
    posteriors['h'] = [h_μ, h_σ]
    i_μ, i_σ = norm.fit(trace['i'])
    posteriors['i'] = [i_μ, i_σ]
    o_μ = []
    o_σ = []
    d_μ = []
    d_σ = []
    for i in range(n_teams):
        oᵢ_μ, oᵢ_σ = norm.fit(trace['o'][:,i])
        o_μ.append(oᵢ_μ)
        o_σ.append(oᵢ_σ)
        dᵢ_μ, dᵢ_σ = norm.fit(trace['d'][:,i])
        d_μ.append(dᵢ_μ)
        d_σ.append(dᵢ_σ)
    posteriors['o'] = [np.array(o_μ), np.array(o_σ)]
    posteriors['d'] = [np.array(d_μ), np.array(d_σ)]
    
    return posteriors

def fatten_priors(prev_posteriors, factor, f_thresh):
    priors = prev_posteriors.copy()
    priors['h'][1] = np.minimum(priors['h'][1] * factor, f_thresh)
    priors['i'][1] = np.minimum(priors['i'][1] * factor, f_thresh)
    priors['o'][1] = np.minimum(priors['o'][1] * factor, f_thresh)
    priors['d'][1] = np.minimum(priors['d'][1] * factor, f_thresh)

    return priors

def model_iteration(obs_data, priors, n_teams, Δσ):
    idₕ = obs_data['idₕ'].to_numpy()
    sₕ_obs = obs_data['sₕ'].to_numpy()
    idₐ = obs_data['idₐ'].to_numpy()
    sₐ_obs = obs_data['sₐ'].to_numpy()
    hw_obs = obs_data['hw'].to_numpy()
    
    with pm.Model():
        # Global model parameters
        h = pm.Normal('h', mu=priors['h'][0], sigma=priors['h'][1])
        i = pm.Normal('i', mu=priors['i'][0], sigma=priors['i'][1])

        # Team-specific poisson model parameters
        o_star_init = pm.Normal('o_star_init', mu=priors['o'][0], sigma=priors['o'][1], shape=n_teams)
        Δ_o = pm.Normal('Δ_o', mu=0.0, sigma=Δσ, shape=n_teams)
        o_star = pm.Deterministic('o_star', o_star_init + Δ_o)
        o = pm.Deterministic('o', o_star - tt.mean(o_star))
                                               
        d_star_init = pm.Normal('d_star_init', mu=priors['d'][0], sigma=priors['d'][1], shape=n_teams)
        Δ_d = pm.Normal('Δ_d', mu=0.0, sigma=Δσ, shape=n_teams)
        d_star = pm.Deterministic('d_star', d_star_init + Δ_d)
        d = pm.Deterministic('d', d_star - tt.mean(d_star))
        
        λₕ = tt.exp(i + h + o[idₕ] - d[idₐ])
        λₐ = tt.exp(i + o[idₐ] - d[idₕ])

        # OT/SO home win bernoulli model parameter
        # P(T < Y), where T ~ a, Y ~ b: a/(a + b)
        pₕ = λₕ/(λₕ + λₐ)
        
        # Likelihood of observed data
        sₕ = pm.Poisson('sₕ', mu=λₕ, observed=sₕ_obs)
        sₐ = pm.Poisson('sₐ', mu=λₐ, observed=sₐ_obs)
        hw = pm.Bernoulli('hw', p=pₕ, observed=hw_obs)

        trace = pm.sample(5000, tune=2000, cores=3, progressbar=True)
        
        posteriors = get_model_posteriors(trace, n_teams)
        
        return posteriors

def model_update(obs_data, priors, n_teams, f, f_thresh, Δσ):
    priors = fatten_priors(priors, f, f_thresh)
    posteriors = model_iteration(obs_data, priors, n_teams, Δσ)

    return posteriors
