import datetime as dt
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')

def game_detail(request, game_pk, date=dt.date.today().strftime("%Y-%m-%d")):
    return render(request, 'game-detail.html')

def teams(request):
    return render(request, 'teams.html')