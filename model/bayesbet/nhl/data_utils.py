import pandas as pd

from bayesbet.logger import get_logger


logger = get_logger(__name__)


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


def extract_shot_data(play_by_play_json):
    home_team_id = play_by_play_json["homeTeam"]["id"]
    goal_x_distance = 89
    goal_y = 0
    last_penalty_time_seconds = 0
    shot_data = []

    plays = play_by_play_json["plays"]
    for previous_play, current_play in zip(plays[:-1], plays[1:]):
        if current_play["typeDescKey"] not in ["shot-on-goal", "goal"]:
            continue
        elif current_play["typeDescKey"] == "penalty":
            last_penalty_period = current_play["periodDescriptor"]["number"]
            last_penalty_time = current_play["timeInPeriod"]
            last_penalty_time_seconds = (last_penalty_period - 1) * 20 * 60 + int(last_penalty_time.split(":")[0]) * 60 + int(last_penalty_time.split(":")[1])
            continue

        goal = current_play["typeDescKey"] == "goal"
        shot_period = current_play["periodDescriptor"]["number"]
        shot_time = current_play["timeInPeriod"]
        shot_time_seconds = (shot_period - 1) * 20 * 60 + int(shot_time.split(":")[0]) * 60 + int(shot_time.split(":")[1])
        shot_detail = current_play["details"]
        is_home_team = shot_detail["eventOwnerTeamId"] == home_team_id
        home_team_defending_side = current_play["homeTeamDefendingSide"]
        if home_team_defending_side == "left":
            if is_home_team:
                goal_x = goal_x_distance
            else:
                goal_x = -goal_x_distance
        elif home_team_defending_side == "right":
            if is_home_team:
                goal_x = -goal_x_distance
            else:
                goal_x = goal_x_distance
        shot_type = shot_detail["shotType"]
        shot_x = shot_detail["xCoord"]
        shot_y = shot_detail["yCoord"]
        shot_distance = ((shot_x - goal_x) ** 2 + (shot_y - goal_y) ** 2) ** 0.5
        shot_angle = (shot_y - goal_y) / max(abs(shot_x - goal_x), 0.1)
        if goal_x < 0:
            shot_angle = -shot_angle
        last_event = previous_play["typeDescKey"]
        last_event_detail = previous_play["details"]
        if "xCoord" in last_event_detail and "yCoord" in last_event_detail:
            last_event_x = last_event_detail["xCoord"]
            last_event_y = last_event_detail["yCoord"]
        else:
            last_event_x = 0
            last_event_y = 0
        last_event_distance = ((last_event_x - shot_x) ** 2 + (last_event_y - shot_y) ** 2) ** 0.5
        last_event_period = previous_play["periodDescriptor"]["number"]
        last_event_time = previous_play["timeInPeriod"]
        last_event_time_seconds = (last_event_period - 1) * 20 * 60 + int(last_event_time.split(":")[0]) * 60 + int(last_event_time.split(":")[1])
        time_since_last_event = shot_time_seconds - last_event_time_seconds
        situation_code = [int(d) for d in str(current_play["situationCode"])]
        away_goalie = situation_code[0]
        away_skaters = situation_code[1]
        home_skaters = situation_code[2]
        home_goalie = situation_code[3]
        if home_skaters != away_skaters and (home_skaters < 5 or away_skaters < 5):
            powerplay_duration = shot_time_seconds - last_penalty_time_seconds
        else:
            powerplay_duration = 0
        opposing_skaters = away_skaters if is_home_team else home_skaters
        current_skaters = home_skaters if is_home_team else away_skaters
        empty_net = (is_home_team and away_goalie == 0) or (not is_home_team and home_goalie == 0)
        
        row = {
            "shot_type": shot_type,
            "shot_x": shot_x,
            "shot_y": shot_y,
            "shot_distance": shot_distance,
            "shot_angle": shot_angle,
            "last_event": last_event,
            "last_event_x": last_event_x,
            "last_event_y": last_event_y,
            "last_event_distance": last_event_distance,
            "time_since_last_event": time_since_last_event,
            "opposing_skaters": opposing_skaters,
            "current_skaters": current_skaters,
            "powerplay_duration": powerplay_duration,
            "empty_net": empty_net,
            "goal": goal,
        }

        shot_data.append(row)
        shot_data = pd.DataFrame(shot_data)
        return shot_data
