import datetime as dt
from django.http import HttpResponse, JsonResponse
from django.db import connections
from django.shortcuts import render

from data.metadata import team_abbrevs, team_colors

import os
from collections import defaultdict
import boto3
from boto3.dynamodb.conditions import Key
endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url=endpoint_url)
table_name = os.getenv('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(table_name)


def games(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('league').eq('nhl') & Key('prediction_date').eq(date)
    )
    games = response['Items'][0]['predictions']
    rows = [{'game_pk':g.game_pk, 'home_team':g.home_team, 'away_team':g.away_team} for g in games]
    return JsonResponse({"data" : rows})


def goal_distribution(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    precision = '.5f'
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('league').eq('nhl') & Key('prediction_date').eq(date)
    )
    games = response['Items'][0]['predictions']
    game = [g for g in games if str(g['game_pk']) == game_pk][0]
    home_dist = game['score_probabilities']['home']
    away_dist = game['score_probabilities']['away']
    goals_dist = []
    for hg, hp in enumerate(home_dist):
        for ag, ap in enumerate(away_dist):
            gp = float(hp)*float(ap)
            goals_dist.append({
                'home_goals':hg, 
                'away_goals':ag,
                'probability':f'{gp:{precision}}'})
    return JsonResponse(goals_dist, safe=False)


def teams(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    response = table.query(
        Limit = 1,
        ReturnConsumedCapacity='TOTAL',
        KeyConditionExpression=
            Key('league').eq('nhl') & Key('prediction_date').eq(date)
    )
    team_data = response['Items'][0]['league_state']['teams']
    teams = []
    for team, mvars in team_data.items():
        row = {'team_name':team, 'team_abb':team_abbrevs[team],
               'team_colors':team_colors[team], 
               'offence_median':mvars['o'][0], 
               'defence_median':mvars['d'][0]}
        teams.append(row)

    return JsonResponse(teams, safe=False)