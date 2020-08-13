import datetime as dt
from django.http import HttpResponse, JsonResponse
from django.db import connections
from django.shortcuts import render

from data.metadata import team_abbrevs, team_colors

import os
from collections import defaultdict
import boto3
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(table_name)


def games(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq('nhl') & Key('PredictionDate').eq(date)
    )
    games = response['Items'][0]['GamePredictions']
    rows = [{'game_pk':g.game_pk, 'home_team':g.home_team, 'away_team':g.away_team} for g in games]
    return JsonResponse({"data" : rows})


def goal_distribution(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    precision = '.5f'
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq('nhl') & Key('PredictionDate').eq(date)
    )
    games = response['Items'][0]['GamePredictions']
    game = [g for g in games if str(g['game_pk']) == game_pk][0]
    home_dist = game['ScoreProbabilities']['home']
    away_dist = game['ScoreProbabilities']['away']
    goals_dist = []
    for hg, hp in enumerate(home_dist):
        for ag, ap in enumerate(away_dist):
            gp = float(hp)*float(ap)
            goals_dist.append({
                'home_goals':hg, 
                'away_goals':ag,
                'probability':f'{gp:{precision}}'})
    return JsonResponse(goals_dist, safe=False)


def game_outcome(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq('nhl') & Key('PredictionDate').eq(date)
    )
    games = response['Items'][0]['GamePredictions']
    game = [g for g in games if str(g['game_pk']) == game_pk][0]
    wp = game['WinPercentages']
    game_outcome = {
        'predictions': {
            'home': [{'type': 'REG', 'value': float(wp[0])},
                        {'type': 'OT', 'value': float(wp[1]) + float(wp[2])}],
            'away': [{'type': 'REG', 'value': float(wp[3])},
                        {'type': 'OT', 'value': float(wp[4]) + float(wp[5])}]
        }
    }
    # Home and away scores
    home_score = game['score']['home']
    away_score = game['score']['away']
    game_outcome['score'] = {
        'home': home_score,
        'away': away_score
    }

    return JsonResponse(game_outcome, safe=False)


def teams(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('League').eq('nhl') & Key('PredictionDate').eq(date)
    )
    team_data = response['Items'][0]['ModelVariables']['teams']
    teams = []
    for team, mvars in team_data.items():
        row = {'team_name':team, 'team_abb':team_abbrevs[team],
               'team_colors':team_colors[team], 
               'offence_median':mvars['o'][0], 
               'defence_median':mvars['d'][0]}
        teams.append(row)

    return JsonResponse(teams, safe=False)