from math import factorial, exp, sqrt, pi
import numpy as np
import pandas as pd
import pymc as pm
from scipy.integrate import quad, dblquad
from scipy.stats import norm

from pydantic import BaseModel

from bayesbet.nhl.data_utils import (
    GamePrediction,
    LeagueState,
    TeamState,
)


t_before_shootout = 5.0/60.0    # 5 minute shootout, divided by regulation time


class ModelVariables(BaseModel):
    i: tuple[float, float]
    h: tuple[float, float]
    o: tuple[list[float], list[float]]
    d: tuple[list[float], list[float]]


class ModelState(BaseModel):
    teams: list[str]
    variables: ModelVariables

    def to_league_state(self) -> LeagueState:
        teams = {}
        for i, t in enumerate(self.teams):
            teams[t] = TeamState(
                o=(
                    self.variables.o[0][i],
                    self.variables.o[1][i],
                ),
                d=(
                    self.variables.d[0][i],
                    self.variables.d[1][i],
                ),
            )
        return LeagueState(
            i=self.variables.i,
            h=self.variables.h,
            teams=teams,
        )
    
    def from_league_state(self, league_state: LeagueState):
        self.teams = list(league_state.teams.keys())
        i = league_state.i
        h = league_state.h
        o_μ = []
        o_σ = []
        d_μ = []
        d_σ = []
        for t in self.teams:
            o_μ.append(league_state.teams[t].o[0])
            o_σ.append(league_state.teams[t].o[1])
            d_μ.append(league_state.teams[t].d[0])
            d_σ.append(league_state.teams[t].d[1])
        self.variables = ModelVariables(
            i=i,
            h=h,
            o=(o_μ, o_σ),
            d=(d_μ, d_σ),
        )

        
class IterativeUpdateModel:
    def __init__(
        self,
        priors: dict | ModelState,
        delta_sigma: float,
        f_thresh: float,
        fattening_factor: float,
    ):
        self.delta_sigma = delta_sigma
        self.f_thresh = f_thresh
        self.fattening_factor = fattening_factor
        if isinstance(priors, ModelState):
            self.priors = priors
        else:
            self.priors = ModelState(**priors)
        
    def get_model_posteriors(self, trace) -> ModelState:
        n_teams = len(self.priors.teams)
        posteriors = {}
        h_μ, h_σ = norm.fit(trace['h'])
        posteriors['h'] = (h_μ, h_σ)
        i_μ, i_σ = norm.fit(trace['i'])
        posteriors['i'] = (i_μ, i_σ)
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
        posteriors['o'] = (o_μ, o_σ)
        posteriors['d'] = (d_μ, d_σ)

        model_variables = ModelVariables(**posteriors)
        
        return ModelState(teams=self.priors.teams, variables=model_variables)

    def fatten_priors(self):
        h_sigma = np.minimum(
            self.priors.variables.h[1] * self.fattening_factor, self.f_thresh
        )
        self.priors.variables.h = (self.priors.variables.h[0], h_sigma)

        i_sigma = np.minimum(
            self.priors.variables.i[1] * self.fattening_factor, self.f_thresh
        )
        self.priors.variables.i = (self.priors.variables.i[0], i_sigma)
        
        o_sigma = np.minimum(
            np.array(self.priors.variables.o[1]) * self.fattening_factor, self.f_thresh
        ).tolist()
        self.priors.variables.o = (self.priors.variables.o[0], o_sigma)

        d_sigma = np.minimum(
            np.array(self.priors.variables.d[1]) * self.fattening_factor, self.f_thresh
        ).tolist()
        self.priors.variables.d = (self.priors.variables.d[0], d_sigma)

    def model_ready_data(self, game_data):
        teams_to_int = {v: i for i, v in enumerate(self.priors.teams)}
        model_data = pd.DataFrame()
        model_data['idₕ'] = game_data['home_team'].replace(teams_to_int)
        model_data['sₕ'] = game_data['home_reg_score']
        model_data['idₐ'] = game_data['away_team'].replace(teams_to_int)
        model_data['sₐ'] = game_data['away_reg_score']
        model_data['hw'] = game_data['home_fin_score'] > game_data['away_fin_score']

        return model_data


    def model_iteration(self, obs_data, samples=5000, tune=2000, cores=1) -> ModelState:
        n_teams = len(self.priors.teams)
        idₕ = obs_data['idₕ'].to_numpy().astype(int)
        sₕ_obs = obs_data['sₕ'].to_numpy().astype(int)
        idₐ = obs_data['idₐ'].to_numpy().astype(int)
        sₐ_obs = obs_data['sₐ'].to_numpy().astype(int)
        hw_obs = obs_data['hw'].to_numpy()
        
        with pm.Model():
            # Global model parameters
            h = pm.Normal('h', mu=self.priors.variables.h[0], sigma=self.priors.variables.h[1])
            i = pm.Normal('i', mu=self.priors.variables.i[0], sigma=self.priors.variables.i[1])

            # Team-specific poisson model parameters
            o_star_init = pm.Normal(
                'o_star_init',
                mu=self.priors.variables.o[0],
                sigma=self.priors.variables.o[1],
                shape=n_teams,
            )
            Δ_o = pm.Normal('Δ_o', mu=0.0, sigma=self.delta_sigma, shape=n_teams)
            o_star = pm.Deterministic('o_star', o_star_init + Δ_o)
            o = pm.Deterministic('o', o_star - o_star.mean())
                                                
            d_star_init = pm.Normal(
                'd_star_init',
                mu=self.priors.variables.d[0],
                sigma=self.priors.variables.d[1],
                shape=n_teams,
            )
            Δ_d = pm.Normal('Δ_d', mu=0.0, sigma=self.delta_sigma, shape=n_teams)
            d_star = pm.Deterministic('d_star', d_star_init + Δ_d)
            d = pm.Deterministic('d', d_star - d_star.mean())
            
            λₕ = pm.math.exp(i + h + o[idₕ] - d[idₐ])
            λₐ = pm.math.exp(i + o[idₐ] - d[idₕ])

            # OT/SO home win bernoulli model parameter
            # P(T < Y), where T ~ a, Y ~ b: a/(a + b)
            pₕ = λₕ/(λₕ + λₐ)
            
            # Likelihood of observed data
            sₕ = pm.Poisson('sₕ', mu=λₕ, observed=sₕ_obs)
            sₐ = pm.Poisson('sₐ', mu=λₐ, observed=sₐ_obs)
            hw = pm.Bernoulli('hw', p=pₕ, observed=hw_obs)

            trace = pm.sample(
                samples,
                tune=tune,
                chains=3,
                cores=cores,
                progressbar=True,
                return_inferencedata=False
            )
        
            posteriors = self.get_model_posteriors(trace)
            
            return posteriors

    def fit(self, games, samples=5000, tune=2000, cores=1):
        self.fatten_priors()
        obs_data = self.model_ready_data(games)
        posteriors = self.model_iteration(
            obs_data, samples=samples, tune=tune, cores=cores
        )
        self.priors = posteriors
        
        return posteriors

    def bayesian_poisson_pdf(self, μ, σ, max_y=10):
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


    def bayesian_bernoulli_win_pdf(self, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
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


    def bayesian_goal_within_time(self, t, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ):
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

    def single_game_prediction(self, game) -> GamePrediction:
        game_pred = {}
        game_pred["game_pk"] = game["game_pk"]
        game_pred["home_team"] = game["home_team"]
        game_pred["away_team"] = game["away_team"]
        game_pred["score"] = {}
        if game["game_state"] == "Final":
            game_pred["score"]["home"] = game["home_fin_score"]
            game_pred["score"]["away"] = game["away_fin_score"]
        else:
            game_pred["score"]["home"] = "-"
            game_pred["score"]["away"] = "-"

        teams_to_int = {v: i for i, v in enumerate(self.priors.teams)}
        idₕ = teams_to_int[game["home_team"]]
        idₐ = teams_to_int[game["away_team"]]
        i_μ = self.priors.variables.i[0]
        i_σ = self.priors.variables.i[1]
        h_μ = self.priors.variables.h[0]
        h_σ = self.priors.variables.h[1]
        oₕ_μ = self.priors.variables.o[0][idₕ]
        oₕ_σ = self.priors.variables.o[1][idₕ]
        oₐ_μ = self.priors.variables.o[0][idₐ]
        oₐ_σ = self.priors.variables.o[1][idₐ]
        dₕ_μ = self.priors.variables.d[0][idₕ]
        dₕ_σ = self.priors.variables.d[1][idₕ]
        dₐ_μ = self.priors.variables.d[0][idₐ]
        dₐ_σ = self.priors.variables.d[1][idₐ]
        # Normal(μ₁,σ₁²) + Normal(μ₂,σ₂²) = Normal(μ₁ + μ₂, σ₁² + σ₂²)
        log_λₕ_μ = i_μ + h_μ + oₕ_μ - dₐ_μ
        log_λₕ_σ = np.sqrt(i_σ ** 2 + h_σ ** 2 + oₕ_σ ** 2 + dₐ_σ ** 2)
        log_λₐ_μ = i_μ + oₐ_μ - dₕ_μ
        log_λₐ_σ = np.sqrt(i_σ ** 2 + oₐ_σ ** 2 + dₕ_σ ** 2)
        home_score_pdf = self.bayesian_poisson_pdf(log_λₕ_μ, log_λₕ_σ)
        away_score_pdf = self.bayesian_poisson_pdf(log_λₐ_μ, log_λₐ_σ)
        game_pred["score_probabilities"] = {
            "home": home_score_pdf,
            "away": away_score_pdf,
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
                    if game["game_type"] != "P":
                        p_ot_win = self.bayesian_goal_within_time(
                            t_before_shootout, log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ
                        )
                        p_so_win = 1.0 - p_ot_win
                    else:
                        p_ot_win = 1.0
                        p_so_win = 0.0
                    pₕ_ot = self.bayesian_bernoulli_win_pdf(
                        log_λₕ_μ, log_λₕ_σ, log_λₐ_μ, log_λₐ_σ
                    )
                    pₐ_ot = 1.0 - pₕ_ot
                    home_ot_win_p += pₕ_ot * p_ot_win * p
                    home_so_win_p += pₕ_ot * p_so_win * p
                    away_ot_win_p += pₐ_ot * p_ot_win * p
                    away_so_win_p += pₐ_ot * p_so_win * p
        win_percentages = {
            "home": {
                "regulation": home_reg_win_p,
                "overtime": home_ot_win_p,
                "shootout": home_so_win_p,
            },
            "away": {
                "regulation": away_reg_win_p,
                "overtime": away_ot_win_p,
                "shootout": away_so_win_p,
            }
        }
        game_pred["win_percentages"] = win_percentages
        return GamePrediction(**game_pred)

    def predict(self, games):
        game_predictions_list = []
        for _, game in games.iterrows():
            game_pred = self.single_game_prediction(game)
            game_predictions_list.append(game_pred)
        return game_predictions_list
