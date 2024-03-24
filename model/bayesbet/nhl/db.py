import logging
import os

import simplejson as json
import boto3
from boto3.dynamodb.conditions import Key
import numpy as np

from bayesbet.logger import get_logger


logger = get_logger(__name__)
region = os.getenv('AWS_REGION')
endpoint_url = os.getenv('AWS_ENDPOINT_URL')
use_ssl = os.getenv('AWS_USE_SSL')


def get_table(table_name):
    dynamodb = boto3.resource('dynamodb', region_name=region, endpoint_url=endpoint_url, use_ssl=use_ssl)
    table = dynamodb.Table(table_name)
    logger.info(f'Connected to table={table_name} in region {region} of endpoint {endpoint_url}')

    return table

def most_recent_dynamodb_item(table_name, hash_key, date):
    table = get_table(table_name)
    logger.info(f'Get most recent item from {table_name} with league={hash_key} and date={date}')
    response = table.query(
        Limit = 1,
        ScanIndexForward = False,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('league').eq(hash_key) & Key('prediction_date').lte(date)
    )
    item_count = len(response['Items'])
    capacity_units = response['ConsumedCapacity']['CapacityUnits']
    logger.info(f'Query consumed {capacity_units} capacity units')
    if item_count > 0:
        most_recent_item = response['Items'][0]
    else:
        most_recent_item = None
    
    return most_recent_item

def query_dynamodb(table_name, start_date, league='nhl'):
    table = get_table(table_name)
    logger.info(f'Get all items from {table_name} with league={league} and start_date={start_date}')
    response = table.query(
        ScanIndexForward = True,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('league').eq(league) & Key('prediction_date').gte(start_date)
    )
    item_count = len(response['Items'])
    capacity_units = response['ConsumedCapacity']['CapacityUnits']
    logger.info(f'Query consumed {capacity_units} capacity units')

    return response['Items']

def put_dynamodb_item(table_name, item):
    table = get_table(table_name)
    league = item['league']
    pred_date = item['prediction_date']
    response = table.put_item(Item=item)
    logger.info(f'Put item into table {table_name} with league={league} and date={pred_date}')
    return response
