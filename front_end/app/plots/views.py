from django.http import HttpResponse, JsonResponse
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
                Key('league').eq('nhl') & Key('prediction_date').lte(date)
        )
    else:
        response = table.query(
            Limit = 1,
            ReturnConsumedCapacity='TOTAL',
            KeyConditionExpression=
                Key('league').eq('nhl') & Key('prediction_date').eq(date)
        )
    return response

def game_outcome_prediction(game):
    wp = game['win_percentages']
    game_outcome = {
        'score':{
            'home': game['outcome']['home_score'],
            'away': game['outcome']['away_score']
        },
        'predictions': {
            'home': [{'type': 'REG', 'value': float(wp['home']['regulation'])},
                        {'type': 'OT', 'value': float(wp['home']['overtime'])},
                        {'type': 'SO', 'value': float(wp['home']['shootout'])}],
            'away': [{'type': 'REG', 'value': float(wp['away']['regulation'])},
                        {'type': 'OT', 'value': float(wp['away']['overtime'])},
                        {'type': 'SO', 'value': float(wp['away']['shootout'])}]
        }
    }
    return game_outcome


def index(request, *callback_args, **callback_kwargs):
    return HttpResponse("Hello, world. You're at the plots index.")

def social_preds(request, *callback_args, **callback_kwargs):
    date=None
    response = get_record(date)
    date = dt.date.fromisoformat(response['Items'][0]['prediction_date']).strftime('%B %d, %Y')
    games = response['Items'][0]['predictions']
    predicted_games = [(i % 2 == 0, {'game_pk':g['game_pk'], 'game_date': date, 
                        'home_team':g['home_team'], 'home_abb':team_abbrevs[g['home_team']],
                        'home_color': team_colors[g['home_team']],
                        'away_team':g['away_team'], 'away_abb':team_abbrevs[g['away_team']],
                        'away_color': team_colors[g['away_team']],
                        'game_pred': game_outcome_prediction(g)
                        }) for i, g in enumerate(games)]
    
    context= {'prediction_date': date, 'predicted_games': predicted_games}
    return render(request, 'plots/social_preds.html', context)

def social_preds_ready(request, *callback_args, **callback_kwargs):
    date=None
    response = get_record(date)
    prediction_date = response['Items'][0]['prediction_date']
    today = dt.datetime.today().strftime("%Y-%m-%d")
    ready_to_post = prediction_date == today

    response = JsonResponse(
        {"ready_to_post" : ready_to_post, "prediction_date" : prediction_date}
    )

    return response
    