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


def prediction(request, game_pk, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    with connections['bayes_bet'].cursor() as cursor:
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