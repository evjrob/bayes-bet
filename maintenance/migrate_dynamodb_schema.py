import boto3

from pydantic import ValidationError
from tqdm import tqdm

from model.bayesbet.nhl.model import ModelState, ModelVariables
from model.bayesbet.nhl.data_model import PredictionRecord, ModelStateRecord, LeagueState


REGION = 'us-east-1'
AWS_PROFILE = 'bayes-bet-admin'
ENVIRONMENT = 'prod'
SOURCE_TABLE_NAME = f'bayes-bet-main-{ENVIRONMENT}'
PRED_TABLE_NAME = f'bayes-bet-predictions-{ENVIRONMENT}'
MODEL_TABLE_NAME = f'bayes-bet-model-state-{ENVIRONMENT}'

session = boto3.Session(profile_name=AWS_PROFILE)
dynamo_client = session.resource('dynamodb', region_name=REGION)

source_table = dynamo_client.Table(SOURCE_TABLE_NAME)
pred_table = dynamo_client.Table(PRED_TABLE_NAME)
model_table = dynamo_client.Table(MODEL_TABLE_NAME)
dynamo_response = source_table.scan()

def migrate_item(item):
    # Try validating the item first
    try:
        PredictionRecord.model_validate(item)
        return item
    except ValidationError:
        item["league"] = item["League"]
        del item["League"]
        
        item["prediction_date"] = item["PredictionDate"]
        del item["PredictionDate"]

        item["deployment_version"] = "legacy"
        del item["ModelMetadata"]

        if "GamePredictions" in item:
            game_predictions = item["GamePredictions"]
            for game in game_predictions:
                outcome = game["score"]
                outcome["home_score"] = outcome["home"]
                outcome["away_score"] = outcome["away"]
                del outcome["home"]
                del outcome["away"]

                game["outcome"] = outcome
                del game["score"]

                game["score_probabilities"] = game["ScoreProbabilities"]
                del game["ScoreProbabilities"]

                original_win_percentages = game["WinPercentages"]
                win_percentages = {
                    "home": {
                        "regulation": original_win_percentages[0],
                        "overtime": original_win_percentages[1],
                        "shootout": original_win_percentages[2],
                    },
                    "away": {
                        "regulation": original_win_percentages[3],
                        "overtime": original_win_percentages[4],
                        "shootout": original_win_percentages[5],
                    },
                }
                game["win_percentages"] = win_percentages
                del game["WinPercentages"]
            
            item["predictions"] = item["GamePredictions"]
            del item["GamePredictions"]
        else:
            item["predictions"] = []
        
        item["league_state"] = item['ModelVariables']
        del item["ModelVariables"]

        if "ModelPerformance" in item:
            model_performance = item["ModelPerformance"]
            prediction_performance = []
            for row in model_performance:
                perf = {
                    "prediction_date": row["date"],
                    "total_games": -1,
                    "cumulative_accuracy": row["cum_acc"],
                    "cumulative_log_loss": row["cum_ll"],
                    "rolling_accuracy": row["rolling_acc"],
                    "rolling_log_loss": row["rolling_ll"],
                }
                prediction_performance.append(perf)
            item["prediction_performance"] = prediction_performance
            del item["ModelPerformance"]
        else:
            item["prediction_performance"] = []

        # Validate item
        validated_item = PredictionRecord.model_validate(item)

        return validated_item.model_dump()

for item in tqdm(dynamo_response['Items']):
    migrated_item = migrate_item(item)
    pred_table.put_item(Item=migrated_item)

while 'LastEvaluatedKey' in dynamo_response:
    dynamo_response = source_table.scan(ExclusiveStartKey=dynamo_response['LastEvaluatedKey'])
    
    for item in tqdm(dynamo_response['Items']):
        migrated_item = migrate_item(item)
        pred_table.put_item(Item=migrated_item)

# Populate the model state table with a record
last_league_state = LeagueState.model_validate(migrated_item["league_state"])
last_model_state = ModelState(
    teams=["A"],
    variables=ModelVariables(
        i=(0,0),
        h=(0,0),
        o=([0], [0]),
        d=([0], [0]),
    ),
)
last_model_state.from_league_state(last_league_state)
model_state_record = ModelStateRecord(
    league="nhl",
    prediction_date=migrated_item["prediction_date"],
    state=last_model_state.model_dump(),
)
model_table.put_item(Item=model_state_record.model_dump())
