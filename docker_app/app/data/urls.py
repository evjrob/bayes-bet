from django.contrib import admin
from django.urls import path, re_path, include

from . import views

urlpatterns = [
    re_path('^(?P<version>(v1|v2))/games/?$', views.games, name="games-today"),
    re_path('^(?P<version>(v1|v2))/games/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))/?$', views.games, name="games-date"),
    re_path('^(?P<version>(v1|v2))/goaldist/(?P<game_pk>\d{10})/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.goal_distribution, name="goal-dist"),
    re_path('^(?P<version>(v1|v2))/gameoutcome/(?P<game_pk>\d{10})/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.game_outcome, name="game-outcome")
]