# Import all of the libraries needed for this post
import logging
import numpy as np
import pandas as pd
import pymc3 as pm
import theano.tensor as tt
import theano
import os
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects import postgresql
import datetime as dt

from src.data.make_dataset import upsert

import boto3
import base64
from botocore.exceptions import ClientError
import json


# AWS code snippet to load secrets from Secret Manager
def get_secret():

    secret_name = "prod/bayes-bet/postgresql-internet"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return json.loads(decoded_binary_secret)

# Modify the data to include team and pair integer labels
def add_team_data_labels(game_data, teams):
    game_data = game_data.merge(teams, left_on='home_team_id', right_on='team', how='left')
    game_data = game_data.rename(columns={'i': 'i_home'}).drop('team', axis=1)
    game_data = game_data.merge(teams, left_on='away_team_id', right_on='team', how='left')
    game_data = game_data.rename(columns={'i': 'i_away'}).drop('team', axis=1)
    
    return game_data

# Run the PYMC model on the input data and return the posterior predictions
# and results for the games in output data.
def model(model_input_data, model_output_data, prediction_game_pks):
    # Get today's date for the prediction_date key
    today = dt.date.today()

    # Extract the unique list of teams and assign an integer label to each one
    input_home_teams = model_input_data.home_team_id.unique()
    input_away_teams = model_input_data.away_team_id.unique()
    output_home_teams = model_output_data.home_team_id.unique()
    output_away_teams = model_output_data.away_team_id.unique()
    teams = np.concatenate((input_home_teams, input_away_teams,
                            output_home_teams, output_away_teams))
    teams = np.unique(teams)
    teams = np.sort(teams)
    teams = pd.DataFrame(teams, columns=['team'])
    teams['i'] = teams.index

    model_input_data = add_team_data_labels(model_input_data, teams)
    model_input_data['home_win'] = model_input_data['home_team_final_score'] > \
                               model_input_data['away_team_final_score']

    model_output_data = add_team_data_labels(model_output_data, teams)

    # Determine the total number of teams for PYMC3
    num_teams = teams.shape[0]

    # Create shaed theano variables that can be swapped out with
    # scheduled games later.
    home_team = theano.shared(model_input_data.i_home.values)
    away_team = theano.shared(model_input_data.i_away.values)

    # Create arrays of observations for our pymc3 model
    observed_home_goals = model_input_data.home_team_regulation_score.values
    observed_away_goals = model_input_data.away_team_regulation_score.values
    observed_home_winner = model_input_data.home_win.values

    # Define the model
    with pm.Model() as model:
        # Global model parameters
        home = pm.Flat('home')
        sd_offence = pm.HalfFlat('sd_offence') #pm.HalfStudentT('sd_offence', nu=3, sd=2.5)
        sd_defence = pm.HalfFlat('sd.offence') #pm.HalfStudentT('sd_defence', nu=3, sd=2.5)
        intercept = pm.Flat('intercept')

        # Team-specific poisson model parameters
        offence_star = pm.Normal('offence_star', mu=0, sd=sd_offence, shape=num_teams)
        defence_star = pm.Normal('defence_star', mu=0, sd=sd_defence, shape=num_teams)
        offence = pm.Deterministic('offence', offence_star - tt.mean(offence_star))
        defence = pm.Deterministic('defence', defence_star - tt.mean(defence_star))
        home_theta = tt.exp(intercept + home + offence[home_team] - defence[away_team])
        away_theta = tt.exp(intercept + offence[away_team] - defence[home_team])

        # OT/SO win bernoulli model parameters
        # https://www.youtube.com/watch?v=0g3pL4Y9MII
        # P(T < Y), where T ~ a, Y ~ b: a/(a + b)
        bernoulli_p_fn = home_theta/(home_theta + away_theta)
        
        # Likelihood of observed data
        home_goals = pm.Poisson('home_goals', mu=home_theta, observed=observed_home_goals)
        away_goals = pm.Poisson('away_goals', mu=away_theta, observed=observed_away_goals)
        tie_breaker = pm.Bernoulli('tie_breaker', p=bernoulli_p_fn, observed=observed_home_winner)

    # Fit the posterior trace
    with model:
        trace = pm.sample(10000, tune=2000, cores=3)

    # Generate model_runs
    bfmi = pm.bfmi(trace)
    max_gr = max(np.max(gr_stats) for gr_stats in pm.gelman_rubin(trace).values())

    model_runs = pd.DataFrame({'prediction_date':today, 
                            'bfmi':bfmi, 
                            'gelman_rubin':max_gr},
                            index=[0])

    # Compute the team_posteriors table
    offence_hpd = pd.DataFrame(pm.stats.hpd(trace['offence']),
                              columns=['offence_hpd_low', 'offence_hpd_high'],
                              index=teams.team.values)
    offence_median = pd.DataFrame(pm.stats.quantiles(trace['offence'])[50],
                                  columns=['offence_median'],
                                  index=teams.team.values)
    offence_hpd = offence_hpd.join(offence_median)
    offence_hpd = offence_hpd.sort_values(by='offence_median')
    offence_hpd = offence_hpd.reset_index()
    offence_hpd.rename(columns={'index':'team_id'}, inplace=True)

    defence_hpd = pd.DataFrame(pm.stats.hpd(trace['defence']),
                              columns=['defence_hpd_low', 'defence_hpd_high'],
                              index=teams.team.values)
    defence_median = pd.DataFrame(pm.stats.quantiles(trace['defence'])[50],
                                  columns=['defence_median'],
                                  index=teams.team.values)
    defence_hpd = defence_hpd.join(defence_median)
    defence_hpd = defence_hpd.sort_values(by='defence_median')
    defence_hpd = defence_hpd.reset_index()
    defence_hpd.rename(columns={'index':'team_id'}, inplace=True)

    offence_for_db = offence_hpd[['team_id', 'offence_median', 'offence_hpd_low', 'offence_hpd_high']]
    defence_for_db = defence_hpd[['team_id', 'defence_median', 'defence_hpd_low', 'defence_hpd_high']]

    team_posteriors = offence_for_db.merge(defence_for_db, how='outer', on='team_id')
    team_posteriors['prediction_date'] = today

    home_hpd = pm.stats.hpd(trace['home'])
    home_hpd_low = home_hpd[0]
    home_hpd_high = home_hpd[1]
    home_median = pm.stats.quantiles(trace['home'])[50]

    intercept_hpd = pm.stats.hpd(trace['intercept'])
    intercept_hpd_low = intercept_hpd[0]
    intercept_hpd_high = intercept_hpd[1]
    intercept_median = pm.stats.quantiles(trace['intercept'])[50]

    general_posteriors = pd.DataFrame({'prediction_date':today,
                                       'home_ice_advantage_median':home_median,
                                       'home_ice_advantage_hpd_low':home_hpd_low,
                                       'home_ice_advantage_hpd_high':home_hpd_high,
                                       'intercept_median':intercept_median,
                                       'intercept_hpd_low':intercept_hpd_low,
                                       'intercept_hpd_high':intercept_hpd_high},
                                       index=[0])

    # Swap theano variables with scheduled games.
    home_team.set_value(model_output_data.i_home.values)
    away_team.set_value(model_output_data.i_away.values)

    with model:
        post_pred = pm.sample_posterior_predictive(trace, samples=5000)

    # Generate the game_predictions
    home_goals_samples = pd.DataFrame(post_pred['home_goals'],
                                      columns=prediction_game_pks)
    home_goals_samples['prediction_number'] = home_goals_samples.index
    home_goals_samples = pd.melt(home_goals_samples, 
                                 id_vars=['prediction_number'],
                                 value_vars=prediction_game_pks.tolist(),
                                 var_name='game_pk', 
                                 value_name='home_team_regulation_goals')

    away_goals_samples = pd.DataFrame(post_pred['away_goals'],
                                      columns=prediction_game_pks)
    away_goals_samples['prediction_number'] = away_goals_samples.index
    away_goals_samples = pd.melt(away_goals_samples, 
                                 id_vars=['prediction_number'],
                                 value_vars=prediction_game_pks.tolist(),
                                 var_name='game_pk', 
                                 value_name='away_team_regulation_goals')

    tiebreaker_samples = pd.DataFrame(post_pred['tie_breaker'],
                                      columns=prediction_game_pks)
    tiebreaker_samples['prediction_number'] = tiebreaker_samples.index
    tiebreaker_samples = pd.melt(tiebreaker_samples, 
                                 id_vars=['prediction_number'],
                                 value_vars=prediction_game_pks.tolist(),
                                 var_name='game_pk', 
                                 value_name='home_wins_after_regulation')


    game_predictions = home_goals_samples.merge(away_goals_samples, 
                                                how='outer', 
                                                on=['game_pk', 'prediction_number'])
    game_predictions = game_predictions.merge(tiebreaker_samples, 
                                              how='outer', 
                                              on=['game_pk', 'prediction_number'])
    game_predictions['prediction_date'] = today

    # Final clean up of results
    model_runs = model_runs[['prediction_date', 'bfmi', 'gelman_rubin']]

    team_posteriors = team_posteriors[['team_id',
                                       'prediction_date',
                                       'offence_median',
                                       'offence_hpd_low',
                                       'offence_hpd_high',
                                       'defence_median',
                                       'defence_hpd_low',
                                       'defence_hpd_high']]

    general_posteriors = general_posteriors[['prediction_date',
                                             'home_ice_advantage_median',
                                             'home_ice_advantage_hpd_low',
                                             'home_ice_advantage_hpd_high',
                                             'intercept_median',
                                             'intercept_hpd_low',
                                             'intercept_hpd_high']]

    game_predictions = game_predictions[['game_pk',
                                         'prediction_date',
                                         'prediction_number',
                                         'home_team_regulation_goals',
                                         'away_team_regulation_goals',
                                         'home_wins_after_regulation']]

    return model_runs, team_posteriors, general_posteriors, game_predictions

# Save the model predictions in postgresql
def write_results_to_db(db_creds, model_runs_data, team_posteriors_data, 
    general_posteriors_data, game_predictions_data):
    DATABASE_USER = db_creds['DATABASE_USER']
    DATABASE_PASSWD = db_creds['DATABASE_PASSWD']
    DATABASE_HOST = db_creds['DATABASE_HOST']
    DATABASE_PORT = db_creds['DATABASE_PORT']
    DATABASE_NAME = db_creds['DATABASE_NAME']

    # Create connection and transaction to sqlite database
    engine = create_engine('postgresql+psycopg2://'+DATABASE_USER+':'+DATABASE_PASSWD+\
        '@'+DATABASE_HOST+':'+DATABASE_PORT+'/'+DATABASE_NAME)
    with engine.begin() as connection:
        metadata = MetaData(engine)

        model_runs_upsert = upsert('model_runs', 
                                   'prediction_date', 
                                   metadata, 
                                   model_runs_data)
        connection.execute(model_runs_upsert)

        team_posteriors_upsert = upsert('team_posteriors', 
                                        ['team_id', 'prediction_date'], 
                                        metadata, 
                                        team_posteriors_data)
        connection.execute(team_posteriors_upsert)

        general_posteriors_upsert = upsert('general_posteriors', 
                                           'prediction_date', 
                                           metadata, 
                                           general_posteriors_data)
        connection.execute(general_posteriors_upsert)

        game_predictions_upsert = upsert('game_predictions', 
                                         ['game_pk', 'prediction_date', 'prediction_number'], 
                                         metadata, 
                                         game_predictions_data)
        connection.execute(game_predictions_upsert)

def main():
    """ Runs the modelling functions to generate results and write them back to
        the appropriate tables in postgresql.
    """
    # Get database credentials from boto3 + Secrets Manager
    db_creds = get_secret()
    DATABASE_USER = db_creds['DATABASE_USER']
    DATABASE_PASSWD = db_creds['DATABASE_PASSWD']
    DATABASE_HOST = db_creds['DATABASE_HOST']
    DATABASE_PORT = db_creds['DATABASE_PORT']
    DATABASE_NAME = db_creds['DATABASE_NAME']

    logger = logging.getLogger(__name__)
    logger.info('Retrieving model input and prediction data')

    # Create connection and transaction to sqlite database
    engine = create_engine('postgresql+psycopg2://'+DATABASE_USER+':'+DATABASE_PASSWD+\
        '@'+DATABASE_HOST+':'+DATABASE_PORT+'/'+DATABASE_NAME)
    connection = engine.connect()

    today = dt.date.today()
    today_str = today.strftime('%Y-%m-%d')
    start_date = (today - dt.timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = (today + dt.timedelta(days=7)).strftime('%Y-%m-%d')

    statement = "SELECT * FROM model_input_data WHERE game_date >= '" + start_date + "';"
    completed_games =  pd.read_sql(statement, connection)

    statement = "SELECT * FROM model_prediction_data WHERE game_date <= '" + end_date + "';"
    scheduled_games =  pd.read_sql(statement, connection)

    connection.close()

    logger.info('Training model on '+start_date+' to '+today_str+' predicting to '+end_date)

    # Select the columns needed specifically for the model
    model_input_data = completed_games[['home_team_id', 
                                        'away_team_id', 
                                        'home_team_regulation_score', 
                                        'away_team_regulation_score', 
                                        'home_team_final_score', 
                                        'away_team_final_score']]

    model_output_data = scheduled_games[['home_team_id', 
                                         'away_team_id']]

    prediction_game_pks = scheduled_games['game_pk']

    model_runs, team_posteriors, general_posteriors, game_predictions = model(model_input_data,
                                                                              model_output_data, 
                                                                              prediction_game_pks)

    logger.info('Writing model results to postgresql')
    
    write_results_to_db(db_creds, model_runs, team_posteriors, general_posteriors, game_predictions)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()