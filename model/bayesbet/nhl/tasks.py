import boto3
import simplejson as json
import logging
import os
import numpy as np
import pandas as pd
import datetime as dt
import s3fs

from requests.api import get

from bayesbet.logger import get_logger
from bayesbet.nhl.data_utils import (
    model_ready_data,
    model_vars_to_numeric,
    model_vars_to_string,
)
from bayesbet.nhl.data_utils import get_teams_int_maps, get_unique_teams
from bayesbet.nhl.db import query_dynamodb, create_dynamodb_item, put_dynamodb_item
from bayesbet.nhl.db import most_recent_dynamodb_item
from bayesbet.nhl.evaluate import update_scores, prediction_performance
from bayesbet.nhl.model import model_update
from bayesbet.nhl.predict import single_game_prediction
from bayesbet.nhl.stats_api import (
    check_for_games,
    fetch_nhl_data_by_date,
    get_season_start_date,
    team_abbrevs,
)


logger = get_logger(__name__)

framework = "pymc"
model_version = "v2.1"
fattening_factor = 1.05  # Expand the posteriors by this amount before using as priors
f_thresh = 0.075  # A cap on team variable standard deviation to prevent blowup
window_size = 1  # The number previous game days used in each iteration
delta_sigma = 0.001  # The standard deviaton of the random walk variables
perf_ws = 14  # Window size for model performance stats
metadata = {
    "framework": framework,
    "model_version": model_version,
    "fattening_factor": str(fattening_factor),
    "window_size": str(window_size),
    "delta_sigma": str(delta_sigma),
}


def create_record(
    bucket_name,
    game_date,
    posteriors,
    int_to_teams,
    game_preds=None,
):
    record = create_dynamodb_item(
        game_date,
        posteriors,
        int_to_teams,
        metadata,
        game_preds=game_preds,
    )
    logger.info(f"Generated new record for League=nhl and date={game_date}")
    put_dynamodb_item(record)

    # Get the pred_dates from s3 and update
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = s3fs.S3FileSystem(
        client_kwargs={
            "endpoint_url": endpoint_url,
            "use_ssl": use_ssl,
        }
    )
    with s3.open(f"{bucket_name}/pred_dates.json", "rb") as f:
        pred_dates = json.load(f)
        pred_dates = pred_dates + [game_date]

    with s3.open(f"{bucket_name}/pred_dates.json", "w") as f:
        json.dump(pred_dates, f)

    return


def ingest_data(bucket_name, pipeline_name, job_id):
    today_dt = dt.date.today()
    today = today_dt.strftime("%Y-%m-%d")

    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = s3fs.S3FileSystem(
        client_kwargs={
            "endpoint_url": endpoint_url,
            "use_ssl": use_ssl,
        }
    )
    
    # Get last_pred
    last_pred = most_recent_dynamodb_item('nhl', today)
    last_pred_date = last_pred['PredictionDate']
    last_pred_dt = dt.date.fromisoformat(last_pred_date)
    logger.info(f'Most recent prediction is from {last_pred_date}')
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/lastpred.json", "w") as f:
        json.dump(last_pred, f)

    teams = sorted(list(team_abbrevs.keys()))
    teams_to_int, int_to_teams = get_teams_int_maps(teams)
    n_teams = len(teams)

    last_pred_games, date_metadata = fetch_nhl_data_by_date(last_pred_date)
    next_game_date = date_metadata["next_game_date"]
    
    def get_next_regular_or_playoff_games(next_game_date):
        games, date_metadata = fetch_nhl_data_by_date(next_game_date)

        # Get the first date of the season
        season_start = None
        current_pred_season = games['season'].max()
        if current_pred_season:
            season_start = get_season_start_date(current_pred_season)
        season_metadata = {
            "current_pred_season": current_pred_season,
            "season_start": season_start,
        }

        # No All Star or other exhibition games
        games = games[games['game_type'].isin(("Pr", "R", "P"))] 

        # Drop games with non-nhl teams (usually preseason exhibition games)
        valid_rows = games["home_team"].isin(teams) & games["away_team"].isin(teams)
        games = games[valid_rows]

        # Drop postponed games
        games = games[games["game_state"] != "Postponed"]  # No Postponed games

        return games, date_metadata, season_metadata
    
    games, date_metadata, season_metadata = get_next_regular_or_playoff_games(
        next_game_date
    )

    # If games are empty, we need to keep searching for the next valid game date
    while games.shape[0]:
        next_game_date = date_metadata["next_game_date"]
        games, date_metadata, season_metadata = get_next_regular_or_playoff_games(
            next_game_date
        )

    current_pred_season = season_metadata["current_pred_season"]
    season_start = season_metadata["season_start"]

    # Save games to S3
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/last_pred_games.csv", "wb") as f:
        last_pred_games.to_csv(f, index=False)

    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/games.csv", "wb") as f:
        games.to_csv(f, index=False)    

    # Get the games that need to be predicted
    pred_idx = (games["game_date"] == next_game_date) & (
        games["game_state"] != "Postponed"
    )
    games_to_predict = games[pred_idx]
    games_to_predict = games_to_predict.to_dict(orient="records")

    return {
        "current_season": int(current_pred_season),
        "last_pred_date": last_pred_date,
        "next_game_date": next_game_date,
        "today": today,
        "games_to_predict": games_to_predict,
        "season_start": season_start,
        "teams": teams,
        "teams_to_int": teams_to_int,
        "int_to_teams": int_to_teams,
        "n_teams": n_teams,
    }


def model_inference(
    bucket_name,
    pipeline_name,
    job_id,
    last_pred_date,
    teams_to_int,
    n_teams,
):
    # Get the games CSV from s3
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = s3fs.S3FileSystem(
        client_kwargs={
            "endpoint_url": endpoint_url,
            "use_ssl": use_ssl,
        }
    )
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/last_pred_games.csv", "rb") as f:
        games = pd.read_csv(f)

    # Get the last record JSON from S3
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/lastpred.json", "rb") as f:
        last_pred = json.load(f)

    # Get last_pred posteriors to use as priors
    priors = last_pred["ModelVariables"]
    priors = model_vars_to_numeric(priors, teams_to_int)

    logger.info(f"Generating new NHL model predictions for {last_pred_date}")

    # Get games from the most recent game date played
    obs_idx = (games["game_date"] == last_pred_date) & (
        games["game_state"] != "Postponed"
    )
    obs_data = games[obs_idx].reset_index(drop=True)
    obs_data = model_ready_data(obs_data, teams_to_int)
    posteriors = model_update(
        obs_data, priors, n_teams, fattening_factor, f_thresh, delta_sigma
    )

    return posteriors


def predict_game(game, posteriors, teams_to_int):
    prediction = single_game_prediction(game, posteriors, teams_to_int)
    return prediction


def update_previous_record(
    bucket_name, pipeline_name, job_id, last_pred_date, season_start
):
    # Get the games CSV from s3
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = s3fs.S3FileSystem(
        client_kwargs={
            "endpoint_url": endpoint_url,
            "use_ssl": use_ssl,
        }
    )
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/last_pred_games.csv", "rb") as f:
        games = pd.read_csv(f)

    # Get the last record JSON from S3
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/lastpred.json", "rb") as f:
        last_pred = json.load(f)

    # Update the scores for the previous record
    updated_last_pred = update_scores(last_pred, games)

    # Update the model performance if it does not exist
    if "ModelPerformance" not in last_pred:
        # Get model performance for the last prediction
        last_pred_dt = dt.date.fromisoformat(last_pred_date)
        if last_pred_date < season_start:
            performance_start_date = (
                last_pred_dt - dt.timedelta(days=perf_ws + 1)
            ).strftime("%Y-%m-%d")
            season_db_records = query_dynamodb(performance_start_date)
        else:
            season_db_records = query_dynamodb(season_start)
        season_db_records[-1] = updated_last_pred
        model_perf = prediction_performance(season_db_records, games, ws=perf_ws)
        number_cols = ["cum_acc", "rolling_acc", "cum_ll", "rolling_ll"]
        model_perf[number_cols] = model_perf[number_cols].applymap("{:,.5f}".format)
        perf_start_date = (last_pred_dt - dt.timedelta(days=perf_ws - 1)).strftime(
            "%Y-%m-%d"
        )
        perf_idx = (model_perf["date"] >= perf_start_date) & (
            model_perf["date"] <= last_pred_date
        )
        model_perf_json = model_perf[perf_idx].to_dict(orient="records")
        updated_last_pred["ModelPerformance"] = model_perf_json
        logger.info(
            "Updated scores and performance for item with "
            f"League=nhl and date={last_pred_date}"
        )

    put_dynamodb_item(updated_last_pred)
    return
