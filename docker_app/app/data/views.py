import datetime as dt
from rest_framework import generics
from django.http import HttpResponse, JsonResponse
from django.db import connections
from django.shortcuts import render

from data.models import Games


def index(request, version='v1'):
    games = Games.objects.filter(game_date='2019-04-15')

    context= {'games': games}
        
    return render(request, 'data/index.html', context)


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


def prediction(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    with connections['data'].cursor() as cursor:
        # Home and away team goal distribution
        goals_query =    """SELECT COALESCE(home.goals, away.goals) as goals, 
                            COALESCE(home_probability, 0) AS home_probability, 
                            COALESCE(away_probability, 0) as away_probability  FROM
                            (SELECT home_team_regulation_goals as goals, count(home_team_regulation_goals)/5000.0 AS home_probability 
                            FROM game_predictions 
                            WHERE game_pk = %s AND prediction_date = %s 
                            GROUP BY game_pk, prediction_date, home_team_regulation_goals) AS home
                            FULL OUTER JOIN
                            (SELECT away_team_regulation_goals as goals, count(away_team_regulation_goals)/5000.0 AS away_probability 
                            FROM game_predictions 
                            WHERE game_pk = %s AND prediction_date = %s
                            GROUP BY game_pk, prediction_date, away_team_regulation_goals) AS away
                            ON home.goals = away.goals
                            ORDER BY home.goals;"""
        cursor.execute(goals_query, [game_pk, date, game_pk, date])
        home_goals = [{'goals':item[0], 'home_probability':float(item[1]), \
            'away_probability':float(item[2])} for item in cursor.fetchall()]

        return JsonResponse(home_goals, safe=False)


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