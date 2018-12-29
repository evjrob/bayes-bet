# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import requests
import json


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
