# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import os
import requests
import json
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects import postgresql
import datetime as dt


# The NHL Statistics API URL
base_url = 'https://statsapi.web.nhl.com'

# Retrieves the JSON current conference data from the NHL stats API
def request_conferences_json():
    path = '/api/v1/conferences/'
    response = requests.get(base_url + path)
    return response.json()

# Retrieves the JSON current division data from the NHL stats API
def request_divisions_json():
    path = '/api/v1/divisions/'
    response = requests.get(base_url + path)
    return response.json()

# Retrieves the JSON current team data from the NHL stats API
def request_teams_json(team_id=None):
    path = '/api/v1/teams/'
    if team_id is not None:
        path = path + str(team_id)
    response = requests.get(base_url + path)
    return response.json()

# Retrieves the JSON game data from the NHL stats API for a 
# selected date range.
def request_games_json(start_date, end_date):
    path = '/api/v1/schedule?startDate='+start_date+\
            '&endDate='+end_date+'&expand=schedule.linescore'
    response = requests.get(base_url + path)
    return response.json()

# Parses the conferences JSON data and extracts the relevant information
# into a pandas dataframe
def extract_conference_data(conferences_json):
    conferences = pd.DataFrame(
        columns=['conference_id',
                 'conference_name',
                 'active'])
    
    for conference in conferences_json['conferences']:
        conference_id = conference['id']
        conference_name = conference['name']
        active = conference['active']

        conferences = conferences.append(
            {'conference_id': conference_id,
             'conference_name': conference_name,
             'active': active},
            ignore_index=True)

    return conferences

# Parses the divisions JSON data and extracts the relevant information
# into a pandas dataframe
def extract_division_data(divisions_json):
    divisions = pd.DataFrame(
        columns=['division_id',
                 'division_name',
                 'division_abbreviation',
                 'conference_id',
                 'active'])
     
    for division in divisions_json['divisions']:
        division_id = division['id']
        division_name = division['name']
        division_abbreviation = division['abbreviation']
        conference_id = division['conference']['id']
        active = division['active']

        divisions = divisions.append(
            {'division_id': division_id,
             'division_name': division_name,
             'division_abbreviation': division_abbreviation,
             'conference_id': conference_id,
             'active': active},
            ignore_index=True)

    return divisions

# Parses the teams JSON data and extracts the relevant information
# into a pandas dataframe
def extract_team_data(teams_json):
    teams = pd.DataFrame(
        columns=['team_id',
                 'team_name',
                 'team_abbreviation',
                 'division_id',
                 'active'])
     
    for team in teams_json['teams']:
        team_id = team['id']
        team_name = team['name']
        team_abbreviation = team['abbreviation']
        if 'id' in team['division']:
            division_id = team['division']['id']
        else:
            division_id = None
        active = team['active']

        teams = teams.append(
            {'team_id': team_id,
             'team_name': team_name,
             'team_abbreviation': team_abbreviation,
             'division_id': division_id,
             'active': active},
            ignore_index=True)

    return teams

# Parses the games JSON data and extracts the relevant information
# into a pandas dataframe
def extract_game_data(games_json):
    games = pd.DataFrame(
        columns=['game_pk',
                 'game_date',
                 'season',
                 'game_type',
                 'game_state',
                 'home_team_id',
                 'away_team_id'])

    periods = pd.DataFrame(
        columns=['game_pk',
                 'period_number',
                 'period_type',
                 'home_goals',
                 'home_shots_on_goal',
                 'away_goals',
                 'away_shots_on_goal'])

    shootouts = pd.DataFrame(
        columns=['game_pk',
                 'home_scores',
                 'home_attempts',
                 'away_scores',
                 'away_attempts'])

    for date in games_json['dates']:
        game_date = date['date']
        for game in date['games']:
            game_pk = game['gamePk']
            season = game['season']
            game_type = game['gameType']
            game_state = game['status']['detailedState']

            home_team = game['teams']['home']['team']
            away_team = game['teams']['away']['team']
            home_team_id = home_team['id']
            away_team_id = away_team['id']

            detailed_score_data = game['linescore']
            periods_list = detailed_score_data['periods']

            for period in periods_list:
                period_number = period['num']
                period_type = period['periodType']
                home_goals = period['home']['goals']
                home_shots_on_goal = period['home']['shotsOnGoal']
                away_goals = period['away']['goals']
                away_shots_on_goal = period['away']['shotsOnGoal']

                periods = periods.append(
                    {'game_pk': game_pk,
                     'period_number': period_number,
                     'period_type': period_type,
                     'home_goals': home_goals,
                     'home_shots_on_goal': home_shots_on_goal,
                     'away_goals': away_goals,
                     'away_shots_on_goal': away_shots_on_goal},
                    ignore_index=True)

            if detailed_score_data['hasShootout'] == True:
                shootout = detailed_score_data['shootoutInfo']
                home_scores = shootout['home']['scores']
                home_attempts = shootout['home']['attempts']
                away_scores = shootout['away']['scores']
                away_attempts = shootout['away']['attempts']

                shootouts = shootouts.append(
                    {'game_pk': game_pk,
                     'home_scores': home_scores,
                     'home_attempts': home_attempts,
                     'away_scores': away_scores,
                     'away_attempts': away_attempts},
                    ignore_index=True)

            games = games.append(
                {'game_pk': game_pk,
                 'game_date': game_date,
                 'season': season,
                 'game_type': game_type,
                 'game_state': game_state,
                 'home_team_id': home_team_id,
                 'away_team_id': away_team_id},
                ignore_index=True)

    return games, periods, shootouts

# Retrieves and extracts the JSON data for teams in the games table that did not
# show up in the current team API call. Usually All-Star or exhibition teams.
def get_missing_team_data(team_id_list):
    missing_team_data = []
    for team_id in team_id_list:
        teams_json = request_teams_json(team_id)
        with open('data/raw/team_'+str(team_id)+'.json', 'w') as outfile:
            json.dump(teams_json, outfile)
        team_data = extract_team_data(teams_json)
        missing_team_data.append(team_data)
    if len(missing_team_data) > 0:
        return pd.concat(missing_team_data, ignore_index=True)
    return None

# Wrap a repeated sqlalchemy upsert statement 
def upsert(table_name, primary_keys, metadata, data):
    # Don't accidentally split a single string primary key
    if type(primary_keys) == str:
        primary_keys = [primary_keys]
    primary_keys = list(primary_keys)
    table = Table(table_name, metadata, autoload=True)
    insert_statement = postgresql.insert(table).values(data.to_dict(orient='records'))
    upsert_statement = insert_statement.on_conflict_do_update(
        index_elements=primary_keys,
        set_={c.key: c for c in insert_statement.excluded if c.key not in primary_keys})
    return upsert_statement

# Handles the retrival, extraction, and database updates for the 
# NHL Stats API data
def update_nhl_data(start_date, end_date):
    conferences_json = request_conferences_json()
    divisions_json = request_divisions_json()
    teams_json = request_teams_json()
    games_json = request_games_json(start_date, end_date)

    with open('data/raw/conferences.json', 'w') as outfile:
        json.dump(conferences_json, outfile)
    with open('data/raw/divisions.json', 'w') as outfile:
        json.dump(divisions_json, outfile)
    with open('data/raw/teams.json', 'w') as outfile:
        json.dump(teams_json, outfile)
    with open('data/raw/games.json', 'w') as outfile:
        json.dump(games_json, outfile)

    # Convert JSON to pandas for database upload.
    conference_data = extract_conference_data(conferences_json)
    division_data = extract_division_data(divisions_json)
    team_data = extract_team_data(teams_json)
    game_data, period_data, shootout_data = extract_game_data(games_json)

    # Retrieve data for any teams in the games table that did not appear in 
    # the teams API call.
    missing_team_ids = game_data['home_team_id'].tolist() + game_data['away_team_id'].tolist()
    missing_team_ids = set(missing_team_ids)
    existing_team_ids = set(team_data['team_id'].tolist())
    missing_team_ids = list(missing_team_ids.difference(existing_team_ids))
    missing_team_data = get_missing_team_data(missing_team_ids)
    if missing_team_data is not None:
        team_data = pd.concat([team_data, missing_team_data], ignore_index=True)

    # Load .env to get database credentials
    project_dir = Path(__file__).resolve().parents[2]
    load_dotenv(find_dotenv())
    DATABASE_USER = os.getenv('DATABASE_USER')
    DATABASE_PASSWD = os.getenv('DATABASE_PASSWD')

    # Create connection and transaction to sqlite database
    engine = create_engine('postgresql+psycopg2://'+DATABASE_USER+':'+DATABASE_PASSWD+'@localhost/bayes_bet')
    with engine.begin() as connection:
        metadata = MetaData(engine)

        conferences_upsert = upsert('conferences', 'conference_id', metadata, conference_data)
        connection.execute(conferences_upsert)

        divisions_upsert = upsert('divisions', 'division_id', metadata, division_data)
        connection.execute(divisions_upsert)

        teams_upsert = upsert('teams', 'team_id', metadata, team_data)
        connection.execute(teams_upsert)

        games_upsert = upsert('games', 'game_pk', metadata, game_data)
        connection.execute(games_upsert)

        periods_upsert = upsert('periods', ('game_pk', 'period_number'), metadata, period_data)
        connection.execute(periods_upsert)

        shootouts_upsert = upsert('shootouts', 'game_pk', metadata, shootout_data)
        connection.execute(shootouts_upsert)

def main():
    """ Retrieves data from the NHL stats API and loads it into the 
        appropriate postgresql tables.
    """
    today = dt.date.today()
    start_date = (today - dt.timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = (today + dt.timedelta(days=365)).strftime('%Y-%m-%d')

    logger = logging.getLogger(__name__)
    logger.info('Retrieving NHL data for '+start_date+' to '+end_date)

    update_nhl_data(start_date, end_date)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
