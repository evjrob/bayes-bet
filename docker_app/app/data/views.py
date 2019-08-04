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
        # Teams playing
        teams_query = """SELECT game_pk, home_team_name, away_team_name 
                        FROM games 
                        LEFT JOIN 
                            (SELECT team_id as home_team_id, team_name as home_team_name
                            FROM teams) AS home_teams
                        ON games.home_team_id = home_teams.home_team_id
                        LEFT JOIN
                            (SELECT team_id as away_team_id, team_name as away_team_name
                            FROM teams) AS away_teams
                        ON games.away_team_id = away_teams.away_team_id
                        WHERE game_pk = %s;"""
        cursor.execute(teams_query, [game_pk])
        item =  cursor.fetchone()
        teams = {'game_pk':item[0], 'home_team_name':item[1], 'away_team_name':item[2]}

        
        # Home team goal distribution
        home_goals_query =   """SELECT home_team_regulation_goals as goals, count(home_team_regulation_goals)/5000.0 AS probability 
                                FROM game_predictions 
                                WHERE game_pk = %s AND prediction_date = %s 
                                GROUP BY game_pk, prediction_date, home_team_regulation_goals 
                                ORDER BY home_team_regulation_goals;"""
        cursor.execute(home_goals_query, [game_pk, date])
        home_goals = [{'goals':item[0], 'probability':float(item[1])} for item in cursor.fetchall()]

        # Away team goal distribution
        away_goals_query =   """SELECT away_team_regulation_goals as goals, count(away_team_regulation_goals)/5000.0 AS probability 
                                FROM game_predictions 
                                WHERE game_pk = %s AND prediction_date = %s 
                                GROUP BY game_pk, prediction_date, away_team_regulation_goals 
                                ORDER BY away_team_regulation_goals;"""
        cursor.execute(away_goals_query, [game_pk, date])
        away_goals = [{'goals':item[0], 'probability':float(item[1])} for item in cursor.fetchall()]

        return JsonResponse(
            {'data': {
                'teams': teams,
                'home_goals': home_goals,
                'away_goals': away_goals
                }
            })