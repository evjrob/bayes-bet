from django.http import HttpResponse
import datetime as dt
from django.shortcuts import render
from django.db import connections

from data.metadata import team_abbrevs, team_colors

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
                        {'type': 'OT', 'value': float(wp[1])},
                        {'type': 'SO', 'value': float(wp[2])}],
            'away': [{'type': 'REG', 'value': float(wp[3])},
                        {'type': 'OT', 'value': float(wp[4])},
                        {'type': 'SO', 'value': float(wp[5])}]
        }
    }
    return game_outcome


def index(request):
    return HttpResponse("Hello, world. You're at the plots index.")

def social_preds(request):
    date=None
    response = get_record(date)
    date = dt.date.fromisoformat(response['Items'][0]['PredictionDate']).strftime('%B %d, %Y')
    games = response['Items'][0]['GamePredictions']
    predicted_games = [(i % 2 == 0, {'game_pk':g['game_pk'], 'game_date': date, 
                        'home_team':g['home_team'], 'home_abb':team_abbrevs[g['home_team']],
                        'home_color': team_colors[g['home_team']],
                        'away_team':g['away_team'], 'away_abb':team_abbrevs[g['away_team']],
                        'away_color': team_colors[g['away_team']],
                        'game_pred': game_outcome_prediction(g)
                        }) for i, g in enumerate(games)]
    
    context= {'prediction_date': date, 'predicted_games': predicted_games}
    return render(request, 'plots/social_preds.html', context)
