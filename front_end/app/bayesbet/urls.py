"""bayesbet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path, re_path

from . import views


urlpatterns = [
    re_path('^(staging|prod)?/?$', views.index),
    re_path('^(staging|prod)?/?(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))/?$', views.index),
    re_path('^(staging|prod)?/?game/(?P<game_pk>\d{10})/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.game_detail),
    re_path('^(staging|prod)?/?teams/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.teams),
    re_path('^(staging|prod)?/?performance/(?P<date>(\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])))?/?$', views.performance),
    re_path('^(staging|prod)?/?data/', include('data.urls')),
    re_path('^(staging|prod)?/?plots/', include('plots.urls')),
]
