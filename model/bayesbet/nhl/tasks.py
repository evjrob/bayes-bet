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
from bayesbet.nhl.predict import game_predictions
from bayesbet.nhl.stats_api import (
    check_for_games,
    fetch_recent_nhl_data,
    fetch_nhl_data_by_dates,
)


logger = get_logger(__name__)

framework = "PyMC3"
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
    gd, posteriors, int_to_teams, teams_to_int, metadata, game_preds=None
):
    record = create_dynamodb_item(
        gd, posteriors, int_to_teams, teams_to_int, metadata, game_preds=game_preds
    )
    logger.info(f"Generated predictions for League=nhl and date={gd}")
    put_dynamodb_item(record)
    return


def ingest_data(bucket_name, pipeline_name, job_id):
    today_dt = dt.date.today()
    today = today_dt.strftime("%Y-%m-%d")
    start_date = (today_dt - dt.timedelta(days=365)).strftime("%Y-%m-%d")

    games = fetch_nhl_data_by_dates(start_date, today)
    games = games[games["game_type"] != "A"]  # No All Star games

    # Get the first date of the season
    current_season = games.loc[games["game_date"] == today]["season"].values[0]
    season_start = games[games["season"] == current_season]["game_date"].min()

    teams = get_unique_teams(games)
    teams_to_int, int_to_teams = get_teams_int_maps(teams)
    n_teams = len(teams)

    # Drop games with non-nhl teams (usually preseason exhibition games)
    valid_rows = games["home_team"].isin(teams) & games["away_team"].isin(teams)
    games = games[valid_rows]

    # Save games to S3
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = s3fs.S3FileSystem(
        client_kwargs={
            "endpoint_url": endpoint_url,
            "use_ssl": use_ssl,
        }
    )
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/games.csv", "wb") as f:
        games.to_csv(f, index=False)

    # Get the last record and save to S3
    last_pred = most_recent_dynamodb_item("nhl", today)
    last_pred_date = last_pred["PredictionDate"]
    logger.info(f"Most recent prediction is from {last_pred_date}")
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/lastpred.json", "w") as f:
        json.dump(last_pred, f)

    # Figure out what the next game date is
    next_game_date = None
    next_games = games[
        (games["game_date"] > last_pred_date) & (games["game_date"] <= today)
    ]
    if next_games.shape[0] > 0:
        next_game_date = next_games["game_date"].min()

    return {
        "current_season": current_season,
        "last_pred_date": last_pred_date,
        "next_game_date": next_game_date,
        "season_start": season_start,
        "teams": teams,
        "teams_to_int": teams_to_int,
        "int_to_teams": int_to_teams,
        "n_teams": n_teams,
    }


def model_inference(games, gd):

    return


def predict():
    return


def update_pred_dates():
    bucket_name = os.getenv("WEB_S3_BUCKET")
    region = os.getenv("AWS_REGION")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = boto3.client(
        "s3", region_name=region, endpoint_url=endpoint_url, use_ssl=use_ssl
    )
    with open("pred_dates.json", "wb") as f:
        s3.download_fileobj(bucket_name, "pred_dates.json", f)

    with open("pred_dates.json", "r") as f:
        pred_dates = json.load(f)
        pred_dates = pred_dates + new_pred_dates

    with open("pred_dates.json", "w") as f:
        f.write(json.dumps(pred_dates))

    with open("pred_dates.json", "rb") as f:
        s3.upload_fileobj(f, bucket_name, "pred_dates.json")
    return


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
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/games.csv", "rb") as f:
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
