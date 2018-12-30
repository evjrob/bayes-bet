CREATE TABLE IF NOT EXISTS conferences (
    conference_id INTEGER PRIMARY KEY,
    conference_name TEXT NOT NULL,
    active BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS divisions (
    division_id INTEGER PRIMARY KEY,
    division_name TEXT NOT NULL,
    division_abbreviation TEXT NOT NULL,
    conference_id INTEGER NOT NULL,
    active BOOLEAN NOT NULL,
    FOREIGN KEY (conference_id) REFERENCES conferences(conference_id)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL,
    team_abbreviation TEXT NOT NULL,
    division_id INTEGER,
    active BOOLEAN NOT NULL,
    FOREIGN KEY (division_id) REFERENCES divisions(division_id)
);

CREATE TABLE IF NOT EXISTS games (
    game_pk INTEGER PRIMARY KEY,
    game_date DATE,
    season TEXT,
    game_type TEXT NOT NULL,
    game_state TEXT NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS periods (
    game_pk INTEGER NOT NULL,
    period_number INTEGER NOT NULL,
    period_type TEXT NOT NULL,
    home_goals INTEGER NOT NULL,
    home_shots_on_goal INTEGER NOT NULL,
    away_goals INTEGER NOT NULL,
    away_shots_on_goal INTEGER NOT NULL,
    PRIMARY KEY (game_pk, period_number),
    FOREIGN KEY (game_pk) REFERENCES games(game_pk)
);

CREATE TABLE IF NOT EXISTS shootouts (
    game_pk INTEGER PRIMARY KEY,
    home_scores INTEGER NOT NULL,
    home_attempts INTEGER NOT NULL,
    away_scores INTEGER NOT NULL,
    away_attempts INTEGER NOT NULL,
    FOREIGN KEY (game_pk) REFERENCES games(game_pk)
);

CREATE TABLE IF NOT EXISTS model_runs (
    prediction_date DATE PRIMARY KEY,
    bfmi REAL NOT NULL,
    gelman_rubin REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS team_posteriors (
    team_id INTEGER NOT NULL,
    prediction_date DATE NOT NULL,
    offence_median REAL NOT NULL,
    offence_hpd_low REAL NOT NULL,
    offense_hpd_high REAL NOT NULL,
    defence_median REAL NOT NULL,
    defence_hpd_low REAL NOT NULL,
    defence_hpd_high REAL NOT NULL,
    PRIMARY KEY (team_id, prediction_date),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (prediction_date) REFERENCES model_runs(prediction_date)
);

CREATE TABLE IF NOT EXISTS general_posteriors (
    prediction_date DATE PRIMARY KEY,
    home_ice_advantage_median REAL NOT NULL,
    home_ice_advantage_hpd_low REAL NOT NULL,
    home_ice_advantage_hpd_high REAL NOT NULL,
    intercept_median REAL NOT NULL,
    intercept_hpd_low REAL NOT NULL,
    intercept_hpd_high REAL NOT NULL,
    FOREIGN KEY (prediction_date) REFERENCES model_runs(prediction_date)
);

CREATE TABLE IF NOT EXISTS game_predictions (
    game_pk INTEGER NOT NULL,
    prediction_date DATE NOT NULL,
    home_team_regulation_goals INTEGER NOT NULL,
    away_team_regulation_goals INTEGER NOT NULL,
    home_wins_after_regulation BOOLEAN NOT NULL,
    PRIMARY KEY (game_pk, prediction_date),
    FOREIGN KEY (game_pk) REFERENCES games(game_pk),
    FOREIGN KEY (prediction_date) REFERENCES model_runs(prediction_date)
)