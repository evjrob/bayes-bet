import datetime as dt
from django.shortcuts import render
from django.db import connections

from data.models import Games, GamePredictions

def get_default_date():
    date = dt.datetime.today() - dt.timedelta(hours=9)
    date = date.strftime("%Y-%m-%d")
    return date

def index(request, date=None):
    if date is None:
        date = get_default_date()
    date_plus = dt.datetime.strptime(date, '%Y-%m-%d') + dt.timedelta(days=2)
    predicted_games = Games.objects.filter(game_date__range=(date, date_plus)).order_by('game_date')
    predicted_games = [{'game_pk':g.game_pk, 'game_date': g.game_date, 
        'home_team':g.home_team.team_name, 'home_abb':g.home_team.team_abbreviation,
        'away_team':g.away_team.team_name, 'away_abb':g.away_team.team_abbreviation} 
        for g in predicted_games]
    #with connections['data'].cursor() as cursor:
    #    query =  """SELECT DISTINCT game_pk, game_date, home_team_name, away_team_name 
    #                FROM games 
    #                LEFT JOIN 
    #                    (SELECT team_id as home_team_id, team_name as home_team_name
    #                    FROM teams) AS home_teams
    #                ON games.home_team_id = home_teams.home_team_id
    #                LEFT JOIN
    #                    (SELECT team_id as away_team_id, team_name as away_team_name
    #                    FROM teams) AS away_teams
    #                ON games.away_team_id = away_teams.away_team_id
    #                WHERE game_date >= %s AND game_date <= %s
    #                ORDER BY game_date;"""
    #    cursor.execute(query, [date, date_plus])
    #    predicted_games = [{'game_pk':g[0], 'game_date': g[1], 
    #        'home_team':g[2], 'away_team':g[3]} for g in cursor.fetchall()]
    context= {'prediction_date': date, 'predicted_games': predicted_games}
    return render(request, 'index.html', context)

def game_detail(request, game_pk, date=None):
    if date is None:
        date = get_default_date()
    game_detail = Games.objects.filter(game_pk=game_pk)
    context= {
        'prediction_date': date, 
        'game_detail': game_detail[0],
        'game_pk': game_pk,
        'home_abb': game_detail[0].home_team.team_abbreviation,
        'away_abb': game_detail[0].away_team.team_abbreviation
    }
    return render(request, 'game-detail.html', context)

def teams(request, date=None):
    if date is None:
        date = get_default_date()
    context= {
        'prediction_date': date
    }
    return render(request, 'teams.html', context)