from django.urls import path, re_path, include

from . import views

urlpatterns = [
    re_path('^(staging|prod)?/?(?P<version>(v1|v2))/games/?(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.games, name="games-date"),
    re_path('^(staging|prod)?/?(?P<version>(v1|v2))/goaldist/(?P<game_pk>\d{10})/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.goal_distribution, name="goal-dist"),
    re_path('^(staging|prod)?/?(?P<version>(v1|v2))/teams/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.teams, name="teams-date")
]