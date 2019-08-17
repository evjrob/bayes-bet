import datetime as dt
from rest_framework import generics
from django.http import HttpResponse, JsonResponse
from django.db import connections
from django.shortcuts import render

from data.models import Games


def games(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    #with connections['data'].cursor() as cursor:
    #    query =  """SELECT DISTINCT game_pk, home_team_name, away_team_name 
    #                FROM games 
    #                LEFT JOIN 
    #                    (SELECT team_id as home_team_id, team_name as home_team_name
    #                    FROM teams) AS home_teams
    #                ON games.home_team_id = home_teams.home_team_id
    #                LEFT JOIN
    #                    (SELECT team_id as away_team_id, team_name as away_team_name
    #                    FROM teams) AS away_teams
    #                ON games.away_team_id = away_teams.away_team_id
    #                WHERE game_date = %s;"""
    #    cursor.execute(query, [date])
    
    games = Games.objects.filter(game_date=date)
    rows = [{'game_pk':g.game_pk, 'home_team':g.home_team.team_name, 'away_team':g.away_team.team_name} for g in games]
    return JsonResponse({"data" : rows})


def goal_distribution(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    with connections['data'].cursor() as cursor:
        # Home and away team goal distribution
        goals_query =    """SELECT home_team_regulation_goals, away_team_regulation_goals, count(*)/5000.0 AS probability 
                            FROM game_predictions 
                            WHERE game_pk = %s AND prediction_date = %s 
                            GROUP BY home_team_regulation_goals, away_team_regulation_goals 
                            ORDER BY home_team_regulation_goals, away_team_regulation_goals;"""
        cursor.execute(goals_query, [game_pk, date])
        goals_dist = [{'home_goals':int(item[0]), 'away_goals':int(item[1]), \
            'probability':float(item[2])} for item in cursor.fetchall()]

        return JsonResponse(goals_dist, safe=False)


def game_outcome(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    with connections['data'].cursor() as cursor:
        # Home and away team goal distribution
        goals_query =    """SELECT AVG((home_team_regulation_goals > away_team_regulation_goals)::Int) AS home_regulation_win,
                            AVG((home_team_regulation_goals = away_team_regulation_goals AND home_wins_after_regulation)::Int) AS home_ot_win,
                            AVG((home_team_regulation_goals = away_team_regulation_goals AND NOT home_wins_after_regulation)::Int) AS away_ot_win,
                            AVG((home_team_regulation_goals < away_team_regulation_goals)::Int) AS away_regulation_win
                            FROM game_predictions WHERE game_pk = %s AND prediction_date = %s;"""
        cursor.execute(goals_query, [game_pk, date])
        row = cursor.fetchone()
        game_outcome = [
            {'label': 'home regulation', 'value': float(row[0])},
            {'label': 'home OT', 'value': float(row[1])},
            {'label': 'away OT', 'value': float(row[2])},
            {'label': 'away regulation', 'value': float(row[3])}
        ]

        return JsonResponse(game_outcome, safe=False)