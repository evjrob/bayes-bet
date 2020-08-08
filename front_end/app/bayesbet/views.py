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


def get_default_date():
    date = dt.datetime.today() - dt.timedelta(hours=9)
    date = date.strftime("%Y-%m-%d")
    return date

def index(request, date=None):
    if date is None:
        date = get_default_date()
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq('nhl') & Key('PredictionDate').eq(date)
    )
    games = response['Items'][0]['GamePredictions']
    predicted_games = [{'game_pk':g['game_pk'], 'game_date': date, 
                        'home_team':g['home_team'], 'home_abb':team_abbrevs[g['home_team']],
                        'away_team':g['away_team'], 'away_abb':team_abbrevs[g['away_team']]
                        } for g in games]

    #predicted_games = Games.objects.filter(game_date__range=(date, date_plus)).order_by('game_date')
    #predicted_games = [{'game_pk':g.game_pk, 'game_date': g.game_date, 
    #    'home_team':g.home_team.team_name, 'home_abb':g.home_team.team_abbreviation,
    #    'away_team':g.away_team.team_name, 'away_abb':g.away_team.team_abbreviation} 
    #    for g in predicted_games]
    context= {'prediction_date': date, 'predicted_games': predicted_games}
    return render(request, 'index.html', context)

def game_detail(request, game_pk, date=None):
    if date is None:
        date = get_default_date()
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq('nhl') & Key('PredictionDate').eq(date)
    )
    games = response['Items'][0]['GamePredictions']
    game = [g for g in games if str(g['game_pk']) == game_pk][0]
    context= {
        'prediction_date': date, 
        'game_detail': game,
        'game_pk': game_pk,
        'home_abb': team_abbrevs[game['home_team']],
        'away_abb': team_abbrevs[game['away_team']]
    }
    return render(request, 'game-detail.html', context)

def teams(request, date=None):
    if date is None:
        date = get_default_date()
    context= {
        'prediction_date': date
    }
    return render(request, 'teams.html', context)