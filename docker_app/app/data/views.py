import datetime as dt
from rest_framework import generics
from django.http import HttpResponse, JsonResponse
from django.db import connections


def index(request, version='v1'):
    return HttpResponse("Hello, world. You're at the data index.")


def games(request, version='v1', date=dt.date.today().strftime("%Y-%m-%d")):
    with connections['bayes_bet'].cursor() as cursor:
        cursor.execute("SELECT DISTINCT game_pk FROM games WHERE game_date = %s;", [date])
        rows = [item[0] for item in cursor.fetchall()]
        return JsonResponse({"data" : rows})