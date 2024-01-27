import logging
import os
import numpy as np
import pandas as pd

from pydantic import BaseModel, field_serializer

from bayesbet.logger import get_logger


logger = get_logger(__name__)


precision = ".5f"

game_type_mapping = {
    1: 'Pr',
    2: 'R',
    3: 'P',
    4: 'A',
    6: 'Other',
    7: 'Other',
    8: 'Other',
    12: 'Other',
}

game_state_mapping = {
    "OFF": "Final",
    "FINAL": "Final",
    "FUT": "Future",
}

team_abbrevs = {
    'Anaheim Ducks':'ANA',
    'Arizona Coyotes':'ARI',
    'Boston Bruins':'BOS',
    'Buffalo Sabres':'BUF',
    'Calgary Flames':'CGY',
    'Carolina Hurricanes':'CAR',
    'Chicago Blackhawks':'CHI',
    'Colorado Avalanche':'COL',
    'Columbus Blue Jackets':'CBJ',
    'Dallas Stars':'DAL',
    'Detroit Red Wings':'DET',
    'Edmonton Oilers':'EDM',
    'Florida Panthers':'FLA',
    'Los Angeles Kings':'LAK',
    'Minnesota Wild':'MIN',
    'Montréal Canadiens':'MTL',
    'Nashville Predators':'NSH',
    'New Jersey Devils':'NJD',
    'New York Islanders':'NYI',
    'New York Rangers':'NYR',
    'Ottawa Senators':'OTT',
    'Philadelphia Flyers':'PHI',
    'Pittsburgh Penguins':'PIT',
    'San Jose Sharks':'SJS',
    'Seattle Kraken':'SEA',
    'St. Louis Blues':'STL',
    'Tampa Bay Lightning':'TBL',
    'Toronto Maple Leafs':'TOR',
    'Vancouver Canucks':'VAN',
    'Vegas Golden Knights':'VGK',
    'Washington Capitals':'WSH',
    'Winnipeg Jets':'WPG',
}
team_names = {v:k for k,v in team_abbrevs.items()}


# Parses the games JSON data and extracts the relevant information
# into a pandas dataframe
def extract_game_data(games_json):
    previous_game_date = games_json["prevDate"]
    next_game_date = games_json["nextDate"]
    games = []

    for game in games_json['games']:
        game_date = game['gameDate']
        game_pk = game['id']
        season = game['season']
        game_type = game['gameType']
        game_state = game['gameState']

        home_team = game['homeTeam']
        away_team = game['awayTeam']
        home_team_name = home_team['abbrev']
        away_team_name = away_team['abbrev']

        if 'score' in home_team and 'score' in away_team:
            home_fin_score = home_team['score']
            away_fin_score = away_team['score']
        else:
            home_fin_score = 0
            away_fin_score = 0

        home_reg_score = home_fin_score
        away_reg_score = away_fin_score

        if "gameOutcome" in game:
            win_type = game["gameOutcome"]["lastPeriodType"]
            if win_type in ["OT", "SO"]:
                if home_fin_score > away_fin_score:
                    home_reg_score -= 1
                elif away_fin_score > home_reg_score:
                    away_reg_score -= 1
        else:
            win_type = "NA"

        games.append(
            {
                'game_pk': game_pk,
                'game_date': game_date,
                'season': season,
                'game_type': game_type,
                'game_state': game_state,
                'home_team': home_team_name,
                'home_reg_score': home_reg_score,
                'home_fin_score': home_fin_score,
                'away_team': away_team_name,
                'away_reg_score': away_reg_score,
                'away_fin_score': away_fin_score,
                'win_type': win_type
            }
        )

    games = pd.DataFrame(games)
    games["game_type"] = games["game_type"].map(game_type_mapping)
    games["game_state"] = games["game_state"].map(game_state_mapping)
    games["home_team"] = games["home_team"].map(team_names)
    games["away_team"] = games["away_team"].map(team_names)

    assert not (
        games["game_type"].isin(["R", "P"]) 
        & (games["home_team"].isnull() | games["away_team"].isnull())
    ).any()

    date_metadata = {
        "previous_game_date": previous_game_date,
        "next_game_date": next_game_date,
    }

    return games, date_metadata


class TeamState(BaseModel):
    o: tuple[float, float]  # (mu, sigma)
    d: tuple[float, float]  # (mu, sigma)

    @field_serializer("o")
    def serialize_o(self, o: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in o)

    @field_serializer("d")
    def serialize_d(self, d: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in d)


class LeagueState(BaseModel):
    i: tuple[float, float]  # (mu, sigma)
    h: tuple[float, float]  # (mu, sigma)
    teams: dict[str, TeamState]

    @field_serializer("i")
    def serialize_i(self, i: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in i)

    @field_serializer("h")
    def serialize_h(self, h: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in h)


class GamePrediction(BaseModel):
    game_pk: int
    home_team: str
    away_team: str
    score: dict[str, int | str]
    score_probabilities: dict[str, list[float]]
    win_percentages: dict[str, dict[str, float]]

    @field_serializer("score_probabilities")
    def serialize_score_probabilities(self, score_probabilities: dict[str, list[float]], _info):
        serialized = {
            k: [f"{v_i:{precision}}" for v_i in v]
            for k, v in score_probabilities.items()
        }
        return serialized

    @field_serializer("win_percentages")
    def serialize_win_percentages(self, win_percentages: list[float], _info):
        serialized = {
            k1: {k2: f"{v2:{precision}}" for k2, v2 in v1.items()}
            for k1, v1 in win_percentages.items()
        }
        return serialized
