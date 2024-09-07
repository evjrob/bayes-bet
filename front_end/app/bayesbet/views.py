import datetime as dt
from django.shortcuts import render
from django.db import connections

from data.metadata import team_abbrevs, team_colors

import os
import boto3
from boto3.dynamodb.conditions import Key
endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url=endpoint_url)
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

def index(request, date=None):
    try:
        response = get_record(date)
        date = response['Items'][0]['prediction_date']
        games = response['Items'][0]['predictions']
        predicted_games = [{'game_pk':g['game_pk'], 'game_date': date, 
                            'home_team':g['home_team'], 'home_abb':team_abbrevs[g['home_team']],
                            'home_color': team_colors[g['home_team']],
                            'away_team':g['away_team'], 'away_abb':team_abbrevs[g['away_team']],
                            'away_color': team_colors[g['away_team']],
                            'game_pred': game_outcome_prediction(g)
                            } for g in games]
    except IndexError:
        predicted_games = []
    context= {'prediction_date': date, 'predicted_games': predicted_games}
    return render(request, 'index.html', context)

def game_detail(request, game_pk, date=None):
    response = get_record(date)
    date = response['Items'][0]['prediction_date']
    games = response['Items'][0]['predictions']
    game = [g for g in games if str(g['game_pk']) == game_pk][0]
    context= {
        'prediction_date': date, 
        'game_detail': game,
        'game_pk': game_pk,
        'home_abb': team_abbrevs[game['home_team']],
        'home_color': team_colors[game['home_team']],
        'away_abb': team_abbrevs[game['away_team']],
        'away_color': team_colors[game['away_team']],
        'game_pred': game_outcome_prediction(game)
    }
    return render(request, 'game-detail.html', context)

def teams(request, date=None):
    response = get_record(date)
    date = response['Items'][0]['prediction_date']
    context= {
        'prediction_date': date
    }
    return render(request, 'teams.html', context)

def performance(request, date=None):
    response = get_record(date)
    if len(response['Items']) == 0 or 'prediction_performance'not in response['Items'][0]:
        context= {
            'has_perf': False,
            'prediction_date': date,
        }
        return render(request, 'performance.html', context)
    else:
        item = response['Items'][0]
        date = item['prediction_date']
        cumulative_accuracy = float(item['prediction_performance'][-1]['cumulative_accuracy']) * 100
        cumulative_accuracy = f'{cumulative_accuracy:.2f}'
        rolling_accuracy = float(item['prediction_performance'][-1]['rolling_accuracy']) * 100
        rolling_accuracy = f'{rolling_accuracy:.2f}'
        cumulative_log_loss = float(item['prediction_performance'][-1]['cumulative_log_loss'])
        rolling_log_loss = float(item['prediction_performance'][-1]['rolling_log_loss'])
        chart_data = item['prediction_performance']
        context= {
            'has_perf': True,
            'prediction_date': date,
            'cumulative_accuracy': cumulative_accuracy,
            'cumulative_log_loss': cumulative_log_loss,
            'rolling_accuracy': rolling_accuracy,
            'rolling_log_loss': rolling_log_loss,
            'chart_data': chart_data
        }
        return render(request, 'performance.html', context)
        