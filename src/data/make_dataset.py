# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import requests
import json
import pandas as pd


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
def request_teams_json():
    path = '/api/v1/teams/'
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
        division_id = team['division']['id']
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
            game_pk = game
            season = game['season']
            game_type = game['gameType']
            game_state = game['status']['detailedState']

            home_team = game['teams']['home']['team']
            away_team = game['teams']['away']['team']
            home_team_id = home_team['id']
            home_team_name = home_team['name']
            away_team_id = away_team['id']
            away_team_name = away_team['name']

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

            if detailed_score_data['hasShootout'] == 'false':
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

    conferences = extract_conference_data(conferences_json)
    divisions = extract_division_data(divisions_json)
    teams = extract_team_data(teams_json)
    games, periods, shootouts = extract_game_data(games_json)

def main():
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    update_nhl_data('2017-09-18', '2018-12-24')

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
