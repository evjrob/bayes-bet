import datetime as dt
from django.shortcuts import render
from django.db import connections

from data.metadata import team_abbrevs

import os
import boto3
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(table_name)


def get_record(date):
    if date is None:
        date = dt.datetime.today() - dt.timedelta(hours=9)
        date = date.strftime("%Y-%m-%d")
        response = table.query(
            Limit = 1,
            ScanIndexForward = False,
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression=
                Key('League').eq('nhl') & Key('PredictionDate').lte(date)
        )
    else:
        response = table.query(
            Limit = 1,
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression=
                Key('League').eq('nhl') & Key('PredictionDate').eq(date)
        )
    return response

def game_outcome_prediction(game):
    wp = game['WinPercentages']
    game_outcome = {
        'score':{
            'home': game['score']['home'],
            'away': game['score']['away']
        },
        'predictions': {
            'home': [{'type': 'REG', 'value': float(wp[0])},
                        {'type': 'OT', 'value': float(wp[1]) + float(wp[2])}],
            'away': [{'type': 'REG', 'value': float(wp[3])},
                        {'type': 'OT', 'value': float(wp[4]) + float(wp[5])}]
        }
    }
    return game_outcome

def index(request, date=None):
    response = get_record(date)
    date = response['Items'][0]['PredictionDate']
    games = response['Items'][0]['GamePredictions']
    predicted_games = [{'game_pk':g['game_pk'], 'game_date': date, 
                        'home_team':g['home_team'], 'home_abb':team_abbrevs[g['home_team']],
                        'away_team':g['away_team'], 'away_abb':team_abbrevs[g['away_team']],
                        'game_pred': game_outcome_prediction(g)
                        } for g in games]
    
    context= {'prediction_date': date, 'predicted_games': predicted_games}
    return render(request, 'index.html', context)

def game_detail(request, game_pk, date=None):
    response = get_record(date)
    date = response['Items'][0]['PredictionDate']
    games = response['Items'][0]['GamePredictions']
    game = [g for g in games if str(g['game_pk']) == game_pk][0]
    context= {
        'prediction_date': date, 
        'game_detail': game,
        'game_pk': game_pk,
        'home_abb': team_abbrevs[game['home_team']],
        'away_abb': team_abbrevs[game['away_team']],
        'game_pred': game_outcome_prediction(game)
    }
    return render(request, 'game-detail.html', context)

def teams(request, date=None):
    response = get_record(date)
    date = response['Items'][0]['PredictionDate']
    context= {
        'prediction_date': date
    }
    return render(request, 'teams.html', context)