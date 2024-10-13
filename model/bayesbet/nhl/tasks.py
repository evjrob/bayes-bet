import asyncio
import aiohttp
import simplejson as json
import os
import pandas as pd
import datetime as dt
import s3fs

from bayesbet.logger import get_logger
from bayesbet.nhl.data_model import (
    PredictionRecord,
    ModelStateRecord,
    GamePrediction,
    PredictionPerformance,
)
from bayesbet.nhl.data_utils import extract_game_data, team_abbrevs
from bayesbet.nhl.db import query_dynamodb, put_dynamodb_item, most_recent_dynamodb_item
from bayesbet.nhl.evaluate import update_scores, prediction_performance
from bayesbet.nhl.model import IterativeUpdateModel, ModelState
from bayesbet.nhl.stats_api import (
    request_games_json as async_request_games_json,
    get_season_start_date as async_get_season_start_date,
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


def request_games_json(date):
    async def make_request(date):
        connector = aiohttp.TCPConnector(limit=1)
        async with aiohttp.ClientSession(connector=connector) as session:
            return await async_request_games_json(session, date)
        
    return asyncio.run(make_request(date))


def get_season_start_date(season):
    async def make_request(season):
        connector = aiohttp.TCPConnector(limit=1)
        async with aiohttp.ClientSession(connector=connector) as session:
            return await async_get_season_start_date(session, season)
        
    return asyncio.run(make_request(season))


def fetch_nhl_data_by_date(date):
    """ 
    Retrieves data from the NHL stats API and loads it into a dataframe.
    """
    logger.info(f'Retrieving NHL data for {date}')

    games_json = request_games_json(date)

    # Convert JSON to pandas for ingestion by model
    game_data, date_metadata = extract_game_data(games_json)

    logger.info('NHL game data successfully retrieved from API')

    return game_data, date_metadata


def create_record(
    bucket_name,
    game_date,
    updated_model_state,
    game_preds,
):
    pred_table_name = os.getenv('DYNAMODB_PRED_TABLE_NAME')
    model_table_name = os.getenv('DYNAMODB_MODEL_TABLE_NAME')
    deployment_version = os.getenv('DEPLOYMENT_VERSION')

    # Update Model State
    model_state = ModelState.model_validate(updated_model_state)
    model_state_record = ModelStateRecord(
        league="nhl",
        prediction_date=game_date,
        state=model_state,
    )
    put_dynamodb_item(model_table_name, model_state_record.model_dump())
    logger.info(f"Generated new model state record for League=nhl and date={game_date}")

    # Update Prediction Record
    predictions = [GamePrediction.model_validate(pred) for pred in game_preds]
    prediction_record = PredictionRecord(
        league="nhl",
        prediction_date=game_date,
        deployment_version=deployment_version,
        league_state=model_state.to_league_state(),
        predictions=predictions,
        prediction_performance=[],
    )
    put_dynamodb_item(pred_table_name, prediction_record.model_dump())
    logger.info(f"Generated new prediction record for League=nhl and date={game_date}")

    # Get the pred_dates from s3 and update
    endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")
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

    endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")
    use_ssl = os.getenv("AWS_USE_SSL")
    s3 = s3fs.S3FileSystem(
        client_kwargs={
            "endpoint_url": endpoint_url,
            "use_ssl": use_ssl,
        }
    )

    pred_table_name = os.getenv('DYNAMODB_PRED_TABLE_NAME')
    model_table_name = os.getenv('DYNAMODB_MODEL_TABLE_NAME')
    
    # Get last_pred
    last_pred = most_recent_dynamodb_item(pred_table_name, 'nhl', today)
    last_model_state = most_recent_dynamodb_item(model_table_name, 'nhl', today)
    last_pred_date = last_pred['prediction_date']
    logger.info(f'Most recent prediction is from {last_pred_date}')
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/lastpred.json", "w") as f:
        json.dump(last_pred, f)
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/last_model_record.json", "w") as f:
        json.dump(last_model_state, f)

    teams = sorted(list(team_abbrevs.keys()))

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
    while games.shape[0] == 0:
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
    }


def model_inference(
    bucket_name,
    pipeline_name,
    job_id,
):
    # Get the games CSV from s3
    endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")
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
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/last_model_record.json", "r") as f:
        last_model_state_record = ModelStateRecord.model_validate_json(f.read())
        last_model_state = last_model_state_record.state

    model = IterativeUpdateModel(
        last_model_state,
        delta_sigma=delta_sigma,
        f_thresh=f_thresh,
        fattening_factor=fattening_factor
    )

    # Filter to only games that have teams the model knows about
    games = games[
        (
            games["home_team"].isin(team_abbrevs.keys())
            & games["away_team"].isin(team_abbrevs.keys())
        )
    ].reset_index(drop=True)

    # Get games from the most recent game date played
    updated_model_state = model.fit(games, cores=1)

    # Update the model state in S3 for later reference if necessary
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/updated_model_state.json", "w") as f:
        f.write(updated_model_state.model_dump_json())

    return updated_model_state.model_dump()


def predict_game(game, updated_model_state):
    model_state = ModelState.model_validate(updated_model_state)
    model = IterativeUpdateModel(
        model_state,
        delta_sigma=delta_sigma,
        f_thresh=f_thresh,
        fattening_factor=fattening_factor
    )
    prediction = model.single_game_prediction(game)
    return prediction.model_dump()


def update_previous_record(
    bucket_name, pipeline_name, job_id, last_pred_date, season_start
):
    # Get the games CSV from s3
    endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")
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
    with s3.open(f"{bucket_name}/{pipeline_name}/{job_id}/lastpred.json", "r") as f:
        last_pred = PredictionRecord.model_validate_json(f.read())

    # Update the scores for the previous record
    updated_last_pred = update_scores(last_pred, games)

    pred_table_name = os.getenv('DYNAMODB_PRED_TABLE_NAME')

    # Update the model performance if it does not exist
    if len(last_pred.prediction_performance) == 0:
        # Get model performance for the last prediction
        last_pred_dt = dt.date.fromisoformat(last_pred_date)
        if last_pred_date < season_start:
            performance_start_date = (
                last_pred_dt - dt.timedelta(days=perf_ws + 1)
            ).strftime("%Y-%m-%d")
            season_db_records = query_dynamodb(pred_table_name, performance_start_date)
        else:
            season_db_records = query_dynamodb(pred_table_name, season_start)
        season_db_records[-1] = updated_last_pred
        season_db_records = [PredictionRecord.model_validate(r) for r in season_db_records]
        model_perf = prediction_performance(season_db_records, games, ws=perf_ws)
        perf_start_date = (last_pred_dt - dt.timedelta(days=perf_ws - 1))
        perf_idx = (model_perf["prediction_date"] >= perf_start_date) & (
            model_perf["prediction_date"] <= last_pred_dt
        )
        model_perf_items = model_perf[perf_idx].to_dict(orient="records")
        model_perf_items = [
            PredictionPerformance.model_validate(item)
            for item in model_perf_items
        ]
        updated_last_pred.prediction_performance = model_perf_items
        logger.info(
            "Updated scores and performance for item with "
            f"League=nhl and date={last_pred_date}"
        )

    put_dynamodb_item(pred_table_name, updated_last_pred.model_dump())
    return last_pred_date
