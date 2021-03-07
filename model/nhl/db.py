import logging
import os

import json
import boto3
from boto3.dynamodb.conditions import Key
import numpy as np

from data_utils import model_vars_to_string


logger = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(table_name)


def most_recent_dynamodb_item(hash_key, date):
    logger.info(f'Get most recent item from {table_name} with League={hash_key} and date={date}')
    response = table.query(
        Limit = 1,
        ScanIndexForward = False,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq(hash_key) & Key('PredictionDate').lte(date)
    )
    item_count = len(response['Items'])
    capacity_units = response['ConsumedCapacity']['CapacityUnits']
    logger.info(f'Query consumed {capacity_units} capacity units')
    if item_count > 0:
        most_recent_item = response['Items'][0]
    else:
        most_recent_item = None
    
    return most_recent_item

def query_dynamodb(start_date, league='nhl'):
    logger.info(f'Get all items from {table_name} with League={league} and start_date={start_date}')
    response = table.query(
        ScanIndexForward = True,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq(league) & Key('PredictionDate').gte(start_date)
    )
    item_count = len(response['Items'])
    capacity_units = response['ConsumedCapacity']['CapacityUnits']
    logger.info(f'Query consumed {capacity_units} capacity units')

    return response['Items']

def create_dynamodb_item(pred_date, posteriors, int_to_teams, teams_to_int, metadata, game_preds=None):
    item = {'League':'nhl', 'PredictionDate':pred_date}
    if game_preds is not None:
        item['GamePredictions'] = game_preds
    model_vars = model_vars_to_string(posteriors, int_to_teams)
    item['ModelVariables'] = model_vars
    item['ModelMetadata'] = metadata

    return item

def put_dynamodb_item(item):
    league = item['League']
    pred_date = item['PredictionDate']
    response = table.put_item(Item=item)
    logger.info(f'Put item into table {table_name} with League=nhl and date={pred_date}')
    return response
