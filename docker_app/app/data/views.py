import datetime as dt
from rest_framework import generics
from django.http import HttpResponse, JsonResponse
from django.db import connections


def index(request, version='v1'):
    return HttpResponse("Hello, world. You're at the data index.")


def games(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    with connections['bayes_bet'].cursor() as cursor:
        query =  """SELECT DISTINCT game_pk, home_team_name, away_team_name 
                    FROM games 
                    LEFT JOIN 
                        (SELECT team_id as home_team_id, team_name as home_team_name
                        FROM teams) AS home_teams
                    ON games.home_team_id = home_teams.home_team_id
                    LEFT JOIN
                        (SELECT team_id as away_team_id, team_name as away_team_name
                        FROM teams) AS away_teams
                    ON games.away_team_id = away_teams.away_team_id
                    WHERE game_date = %s;"""
        cursor.execute(query, [date])
        rows = [{'game_pk':item[0], 'home_team':item[1], 'away_team':item[2]} for item in cursor.fetchall()]
        return JsonResponse({"data" : rows})